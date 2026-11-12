"""Pedido, geração, arquivo e verificação de documentos (FR-001 a FR-018 da feature 006).

O pedido nasce na tela e a geração roda no worker Celery; a versão aprovada usa só o conteúdo
congelado e o layout dela; o PDF oficial é selado e leva o código de verificação.
"""

import hashlib
import logging

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.text import slugify

from sgp.audit.services import record_event
from sgp.core.access import can_access_project
from sgp.files.storage import IntegrityFailure, record_integrity_failure, store_bytes
from sgp.projects.permissions import can_view_financials
from sgp.signatures.documents import APPROVED, get_adapter, load
from sgp.signatures.models import ApprovedVersion, DocumentKind

from . import content as content_module
from . import render_docx, render_pdf, seal
from .layouts import LogoIntegrityError, layout_for
from .models import (
    ACTIVE_STATUSES,
    GeneratedDocument,
    GenerationRequest,
    OutputFormat,
    RequestStatus,
)

logger = logging.getLogger(__name__)
CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
NO_ACCESS = "Você não tem acesso a este documento."
KIND_LABELS = {
    DocumentKind.SUBDOCUMENT: "Subdocumento",
    DocumentKind.CHARTER: "Termo de Abertura de Projeto",
    DocumentKind.BUSINESS_PLAN: "Plano de Negócios",
}


# ------------------------------------------------------------------ permissões


def can_view_document(user, kind: str, obj) -> bool:
    """Quem vê o documento gera e baixa (FR-003); Plano de Negócios exige dados financeiros."""
    project = get_adapter(kind).project(obj)
    if not can_access_project(user, project):
        return False
    if kind == DocumentKind.BUSINESS_PLAN:
        return can_view_financials(user, project)
    return True


def object_type(kind: str) -> str:
    return f"documents.{kind}"


def _event(event_type, kind, obj, by, **kwargs):
    adapter = get_adapter(kind)
    return record_event(
        event_type,
        actor=by,
        object_type=object_type(kind),
        object_id=obj.pk,
        object_repr=adapter.title(obj)[:255],
        project_id=adapter.project(obj).pk,
        **kwargs,
    )


# ------------------------------------------------------------------ código de verificação


def verification_code(kind: str, object_id: int, version: int, digest: str, layout_id: int) -> str:
    """16 caracteres base32 de Crockford em grupos de 4, estáveis na regeneração (research R9)."""
    raw = hashlib.sha256(f"{kind}:{object_id}:{version}:{digest}:{layout_id}".encode()).digest()
    number = int.from_bytes(raw[:10], "big")
    chars = []
    for _ in range(16):
        chars.append(CROCKFORD[number & 31])
        number >>= 5
    code = "".join(reversed(chars))
    return "-".join(code[index : index + 4] for index in range(0, 16, 4))


def normalize_code(text: str) -> str:
    cleaned = "".join(ch for ch in (text or "").upper() if ch.isalnum())
    cleaned = cleaned.replace("O", "0").replace("I", "1").replace("L", "1")
    if len(cleaned) != 16 or any(ch not in CROCKFORD for ch in cleaned):
        return ""
    return "-".join(cleaned[index : index + 4] for index in range(0, 16, 4))


# ------------------------------------------------------------------ pedido


def request_generation(kind: str, obj, fmt: str, *, by, request=None) -> GenerationRequest:
    """Cria (ou reaproveita, se já há um em andamento) o pedido e o enfileira (FR-002)."""
    if fmt not in OutputFormat.values:
        raise ValidationError("Formato inexistente.")
    adapter = get_adapter(kind)
    obj = adapter.get(obj.pk)
    if not can_view_document(by, kind, obj):
        raise PermissionDenied(NO_ACCESS)
    version = adapter.version(obj)
    official = fmt == OutputFormat.PDF and adapter.status(obj) == APPROVED
    active = GenerationRequest.objects.filter(
        kind=kind, object_id=obj.pk, version=version, format=fmt, status__in=ACTIVE_STATUSES
    ).first()
    if active:
        return active
    try:
        with transaction.atomic():
            pending = GenerationRequest.objects.create(
                kind=kind,
                object_id=obj.pk,
                project=adapter.project(obj),
                version=version,
                format=fmt,
                official=official,
                requested_by=by,
            )
            _event(
                "documents.requested",
                kind,
                obj,
                by,
                new_value={
                    "pedido": pending.pk,
                    "formato": fmt,
                    "versao": f"{version:02d}",
                    "oficial": official,
                },
                request=request,
            )
    except IntegrityError:
        return GenerationRequest.objects.get(
            kind=kind, object_id=obj.pk, version=version, format=fmt, status__in=ACTIVE_STATUSES
        )
    from . import tasks

    transaction.on_commit(lambda: tasks.generate.delay(pending.pk))
    return pending


# ------------------------------------------------------------------ geração


def _approved(kind: str, object_id: int, version: int) -> ApprovedVersion:
    try:
        return ApprovedVersion.objects.get(kind=kind, object_id=object_id, version=version)
    except ApprovedVersion.DoesNotExist:
        raise ValidationError(
            "Esta versão foi aprovada sem a assinatura eletrônica (antes da feature 005); "
            "o PDF oficial não pode ser emitido. Crie nova versão e aprove com assinatura."
        ) from None


def _frozen_content(kind: str, obj, version: int):
    rendering = content_module.frozen(kind, obj.pk, version)
    if rendering is None:  # aprovação anterior à feature 006
        rendering = content_module.freeze(kind, obj, approved=_approved(kind, obj.pk, version))
    return rendering


def _file_name(content: dict, fmt: str) -> str:
    base = slugify(f"{content.get('project_code') or 'projeto'} {content['title']}")
    return f"{base}-v{content['version']}.{fmt}"


def _iso(moment) -> str:
    return timezone.localtime(moment).replace(microsecond=0).isoformat()


def generate(pending: GenerationRequest) -> GeneratedDocument:
    adapter, obj = load(pending.kind, pending.object_id)
    version = adapter.version(obj)
    if version != pending.version:
        raise ValidationError("O documento mudou de versão depois do pedido; peça de novo.")
    status = adapter.status(obj)
    approved = status == APPROVED
    if approved:
        rendering = _frozen_content(pending.kind, obj, version)
        content, layout, digest = rendering.content, rendering.layout, rendering.content_hash
        created = _iso(rendering.created_at)
    else:
        layout = layout_for(pending.kind, obj.pk, version)
        content = content_module.build(pending.kind, obj, layout)
        digest = ""
        created = _iso(pending.requested_at)
    code = ""
    if pending.format == OutputFormat.PDF:
        if approved:
            code = verification_code(pending.kind, obj.pk, version, digest, layout.pk)
        data = render_pdf.render(
            content,
            layout,
            draft=not approved,
            created=created,
            identifier=render_pdf.identifier_for(pending.kind, obj.pk, version, layout.pk, digest),
            verification_code=code,
        )
    else:
        moment = rendering.created_at if approved else pending.requested_at
        data = render_docx.render(
            content,
            layout,
            draft=not approved,
            created=timezone.localtime(moment).replace(tzinfo=None),
        )
    content_digest = hashlib.sha256(data).hexdigest()
    final = seal.seal(data) if pending.official else data
    stored = store_bytes(
        final,
        name=_file_name(content, pending.format),
        kind=pending.format,
        by=pending.requested_by,
    )
    same_as_first = None
    if pending.official:
        first = (
            GeneratedDocument.objects.filter(
                kind=pending.kind,
                object_id=obj.pk,
                version=version,
                official=True,
                layout=layout,
            )
            .order_by("generated_at", "pk")
            .first()
        )
        same_as_first = first is None or first.content_hash == content_digest
        if not same_as_first:
            _event(
                "documents.regeneration_mismatch",
                pending.kind,
                obj,
                pending.requested_by,
                old_value={"resumo_conteudo": first.content_hash},
                new_value={"resumo_conteudo": content_digest},
            )
    generated = GeneratedDocument.objects.create(
        kind=pending.kind,
        object_id=obj.pk,
        project=adapter.project(obj),
        version=version,
        document_status=status,
        format=pending.format,
        official=pending.official,
        form_template_id=content.get("form_template"),
        layout=layout,
        data_version=getattr(obj, "row_version", 0) or 0,
        file=stored,
        content_hash=content_digest,
        file_hash=stored.sha256,
        verification_code=code,
        same_as_first=same_as_first,
        generated_by=pending.requested_by,
    )
    _event(
        "documents.generated",
        pending.kind,
        obj,
        pending.requested_by,
        new_value={
            "pedido": pending.pk,
            "arquivo": stored.pk,
            "formato": pending.format,
            "versao": f"{version:02d}",
            "situacao": status,
            "oficial": pending.official,
            "modelo_formulario": content.get("form_template"),
            "modelo_layout": layout.version_display,
            "resumo_conteudo": content_digest,
            "resumo_arquivo": stored.sha256,
            "codigo": code,
            "igual_a_anterior": same_as_first,
        },
    )
    return generated


FRIENDLY_ERRORS = (seal.SealError, ValidationError, LogoIntegrityError, IntegrityFailure)


def _friendly(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        return "; ".join(exc.messages)
    if isinstance(exc, IntegrityFailure):
        return "Um arquivo usado no documento (logotipo ou anexo) falhou na conferência de integridade."
    if isinstance(exc, FRIENDLY_ERRORS):
        return str(exc)
    return "Falha inesperada na geração; a TI foi avisada pela trilha de auditoria."


def run_request(request_id: int) -> GenerationRequest:
    """Executa o pedido (worker). Nunca levanta: falha vira situação "Falhou" com alerta."""
    with transaction.atomic():
        pending = GenerationRequest.objects.select_for_update().get(pk=request_id)
        if pending.status != RequestStatus.QUEUED:
            return pending
        pending.status = RequestStatus.RUNNING
        pending.started_at = timezone.now()
        pending.save(update_fields=["status", "started_at"])
    try:
        with transaction.atomic():
            generated = generate(pending)
            pending.status = RequestStatus.DONE
            pending.result = generated
            pending.finished_at = timezone.now()
            pending.save(update_fields=["status", "result", "finished_at"])
    except Exception as exc:  # noqa: BLE001 - toda falha fica registrada e visível
        if not isinstance(exc, FRIENDLY_ERRORS):
            logger.exception("Falha na geração do pedido %s", request_id)
        if isinstance(exc, IntegrityFailure):
            record_integrity_failure(exc)
        message = _friendly(exc)
        with transaction.atomic():
            pending.status = RequestStatus.FAILED
            pending.error = message
            pending.finished_at = timezone.now()
            pending.save(update_fields=["status", "error", "finished_at"])
            adapter, obj = load(pending.kind, pending.object_id)
            _event(
                "documents.generation_failed",
                pending.kind,
                obj,
                pending.requested_by,
                new_value={
                    "pedido": pending.pk,
                    "formato": pending.format,
                    "versao": pending.version_display,
                    "erro": message,
                },
            )
    return pending


# ------------------------------------------------------------------ consulta


def history(kind: str, obj):
    return GeneratedDocument.objects.filter(kind=kind, object_id=obj.pk).select_related(
        "layout", "form_template", "generated_by", "file"
    )


def active_requests(kind: str, obj):
    return GenerationRequest.objects.filter(
        kind=kind, object_id=obj.pk, status__in=ACTIVE_STATUSES
    ).order_by("-requested_at")


def record_download(generated: GeneratedDocument, *, by, request=None) -> None:
    adapter, obj = load(generated.kind, generated.object_id)
    _event(
        "documents.downloaded",
        generated.kind,
        obj,
        by,
        new_value={
            "arquivo": generated.file_id,
            "formato": generated.format,
            "versao": generated.version_display,
            "oficial": generated.official,
        },
        request=request,
    )


def integrity_failed(failure: IntegrityFailure, request=None) -> None:
    record_integrity_failure(failure, request=request)


def lookup(code_text: str, *, user, request=None) -> dict:
    """Consulta do código de verificação (FR-014); sem acesso, só a validade e o resumo."""
    code = normalize_code(code_text)
    documents = list(
        GeneratedDocument.objects.filter(verification_code=code, official=True).order_by(
            "generated_at", "pk"
        )
        if code
        else []
    )
    result = {"code": code or (code_text or "").strip()[:30], "found": bool(documents)}
    access = False
    project_id = None
    if documents:
        first = documents[0]
        adapter, obj = load(first.kind, first.object_id)
        access = can_view_document(user, first.kind, obj)
        approved = _approved(first.kind, first.object_id, first.version)
        newer = (
            ApprovedVersion.objects.filter(
                kind=first.kind, object_id=first.object_id, version__gt=first.version
            )
            .order_by("-version")
            .first()
        )
        rendering = content_module.frozen(first.kind, first.object_id, first.version)
        result.update(
            {
                "kind_label": KIND_LABELS.get(first.kind, first.kind),
                "title": rendering.content["title"] if rendering else "",
                "version": first.version_display,
                "situation": f"Substituída pela versão {newer.version:02d}" if newer else "Vigente",
                "approved_on": timezone.localtime(approved.approved_at).strftime("%d/%m/%Y"),
                "signatures": rendering.content.get("signatures", []) if rendering else [],
                "files": documents,
                "access": access,
                "project": adapter.project(obj) if access else None,
            }
        )
        project_id = adapter.project(obj).pk if access else None
    record_event(
        "documents.verification_lookup",
        actor=user,
        object_type="documents.verification",
        object_id=result["code"][:64],
        object_repr=result["code"][:255],
        project_id=project_id,
        new_value={"codigo": result["code"], "encontrado": result["found"], "com_acesso": access},
        request=request,
    )
    return result
