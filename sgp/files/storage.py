"""Armazenamento de arquivos com resumo SHA-256 conferido a cada leitura (FR-020 da feature 003).

O conteúdo fica em MEDIA_ROOT/aa/bb/<sha256> (endereçado pelo conteúdo) e os metadados em
StoredFile, somente de inclusão. O tipo é conferido pela assinatura do arquivo e pela extensão.
"""

import hashlib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError

from sgp.audit.services import record_event

from .models import StoredFile

CHUNK = 1024 * 1024
NUL = bytes([0])
PNG_SIGNATURE = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
JPEG_SIGNATURE = bytes([0xFF, 0xD8, 0xFF])
ZIP_SIGNATURE = bytes([0x50, 0x4B, 0x03, 0x04])


@dataclass(frozen=True)
class FileKind:
    code: str
    label: str
    content_type: str
    extensions: tuple[str, ...]

    def matches(self, head: bytes) -> bool:
        if self.code == "pdf":
            return head.startswith(b"%PDF-")
        if self.code == "png":
            return head.startswith(PNG_SIGNATURE)
        if self.code == "jpeg":
            return head.startswith(JPEG_SIGNATURE)
        if self.code in ("xlsx", "docx"):
            return head.startswith(ZIP_SIGNATURE)
        if self.code == "csv":
            return NUL not in head
        return False


KINDS = {
    kind.code: kind
    for kind in (
        FileKind("pdf", "PDF", "application/pdf", (".pdf",)),
        FileKind("png", "PNG", "image/png", (".png",)),
        FileKind("jpeg", "JPEG", "image/jpeg", (".jpg", ".jpeg")),
        FileKind(
            "xlsx",
            "XLSX",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            (".xlsx",),
        ),
        FileKind("csv", "CSV", "text/csv", (".csv",)),
        FileKind(
            "docx",
            "DOCX",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            (".docx",),
        ),
    )
}
DOCUMENT_KINDS = ("pdf", "png", "jpeg")
GENERATED_KINDS = ("pdf", "docx")  # só gerados pelo sistema (feature 006), nunca aceitos em upload
SPREADSHEET_KINDS = ("csv", "xlsx")
DOCUMENTS = None  # tipos de anexo de documento habilitados em FILE_DOCUMENT_TYPES
HEAD_SIZE = 4096


class IntegrityFailure(Exception):
    """O conteúdo guardado não confere com o resumo registrado."""

    def __init__(self, stored: StoredFile, actual: str):
        super().__init__(f"Resumo divergente no arquivo {stored.pk}")
        self.stored = stored
        self.actual = actual


def max_bytes() -> int:
    return int(settings.FILE_MAX_MB) * 1024 * 1024


def media_root() -> Path:
    return Path(settings.MEDIA_ROOT)


def _kind_labels(allowed) -> str:
    return ", ".join(KINDS[code].label for code in allowed)


def _read_head(uploaded) -> bytes:
    uploaded.seek(0)
    head = uploaded.read(HEAD_SIZE)
    uploaded.seek(0)
    return head


def document_kinds() -> tuple[str, ...]:
    """Tipos de anexo de documento habilitados (FR-020), sempre dentro dos conhecidos."""
    configured = [str(code).strip().lower() for code in settings.FILE_DOCUMENT_TYPES]
    return tuple(code for code in DOCUMENT_KINDS if code in configured)


def check_upload(uploaded, allowed=DOCUMENTS) -> FileKind:
    """Confere tamanho, extensão e assinatura do arquivo; devolve o tipo reconhecido."""
    allowed = document_kinds() if allowed is DOCUMENTS else tuple(allowed)
    if not allowed:
        raise ValidationError("Nenhum tipo de anexo está habilitado; avise a TI.")
    size = getattr(uploaded, "size", None) or 0
    if size == 0:
        raise ValidationError("O arquivo está vazio.")
    if size > max_bytes():
        raise ValidationError(
            f"O arquivo tem {size / (1024 * 1024):.1f} MB e o máximo é "
            f"{settings.FILE_MAX_MB} MB.".replace(".", ",", 1)
        )
    name = os.path.basename(uploaded.name or "").lower()
    head = _read_head(uploaded)
    for code in allowed:
        kind = KINDS[code]
        if name.endswith(kind.extensions) and kind.matches(head):
            return kind
    raise ValidationError(f"Tipo de arquivo não aceito. Aceitos: {_kind_labels(allowed)}.")


def store_upload(uploaded, *, by, allowed=DOCUMENTS) -> StoredFile:
    """Grava o conteúdo pelo SHA-256 e registra o arquivo e o evento files.uploaded."""
    kind = check_upload(uploaded, allowed)
    root = media_root()
    temp_dir = root / "tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    size = 0
    uploaded.seek(0)
    with tempfile.NamedTemporaryFile(dir=temp_dir, delete=False) as temp:
        for chunk in uploaded.chunks(CHUNK) if hasattr(uploaded, "chunks") else [uploaded.read()]:
            digest.update(chunk)
            size += len(chunk)
            temp.write(chunk)
    sha256 = digest.hexdigest()
    storage_name = f"{sha256[:2]}/{sha256[2:4]}/{sha256}"
    target = root / storage_name
    if target.exists():
        os.remove(temp.name)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(temp.name, target)
    stored = StoredFile.objects.create(
        sha256=sha256,
        original_name=os.path.basename(uploaded.name)[:255],
        content_type=kind.content_type,
        size=size,
        storage_name=storage_name,
        uploaded_by=by,
    )
    record_event(
        "files.uploaded",
        actor=by,
        obj=stored,
        new_value={
            "nome": stored.original_name,
            "tipo": stored.content_type,
            "tamanho": stored.size,
            "sha256": sha256,
        },
    )
    return stored


def store_bytes(data: bytes, *, name: str, kind: str, by) -> StoredFile:
    """Grava um arquivo gerado pelo sistema (feature 006), endereçado pelo SHA-256.

    O evento de negócio (ex.: documents.generated) é registrado por quem gera, com o resumo.
    """
    if kind not in GENERATED_KINDS or not KINDS[kind].matches(data[:HEAD_SIZE]):
        raise ValidationError("Conteúdo gerado não corresponde ao tipo informado.")
    sha256 = hashlib.sha256(data).hexdigest()
    root = media_root()
    storage_name = f"{sha256[:2]}/{sha256[2:4]}/{sha256}"
    target = root / storage_name
    if not target.exists():
        temp_dir = root / "tmp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=temp_dir, delete=False) as temp:
            temp.write(data)
        target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(temp.name, target)
    return StoredFile.objects.create(
        sha256=sha256,
        original_name=os.path.basename(name)[:255],
        content_type=KINDS[kind].content_type,
        size=len(data),
        storage_name=storage_name,
        uploaded_by=by,
    )


def read_verified(stored: StoredFile) -> bytes:
    """Lê o conteúdo e confere o SHA-256; arquivo ausente ou alterado levanta IntegrityFailure."""
    path = media_root() / stored.storage_name
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        raise IntegrityFailure(stored, "arquivo ausente") from None
    actual = hashlib.sha256(data).hexdigest()
    if actual != stored.sha256:
        raise IntegrityFailure(stored, actual)
    return data


def record_integrity_failure(failure: IntegrityFailure, *, request=None) -> None:
    record_event(
        "files.integrity_failed",
        obj=failure.stored,
        old_value={"sha256": failure.stored.sha256},
        new_value={"sha256": failure.actual},
        request=request,
    )
