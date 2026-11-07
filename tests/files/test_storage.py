"""Armazenamento de arquivos com SHA-256 conferido na leitura (FR-020, SC-005 da feature 003)."""

import hashlib
from pathlib import Path

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import ProgrammingError

from sgp.files import storage
from sgp.files.models import StoredFile
from tests.db_helpers import app_role_exists, run_as_app_role

pytestmark = [pytest.mark.django_db]

PDF = b"%PDF-1.7\nconteudo de teste\n%%EOF\n"
PNG = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]) + b"resto-da-imagem"
JPEG = bytes([0xFF, 0xD8, 0xFF, 0xE0]) + b"resto-da-imagem"


def upload(name, content, content_type="application/octet-stream"):
    return SimpleUploadedFile(name, content, content_type=content_type)


@pytest.fixture
def person(make_user):
    return make_user()


@pytest.mark.req("003:FR-020")
def test_guarda_pelo_sha256_e_registra_o_evento(person, settings, events):
    stored = storage.store_upload(upload("laudo.pdf", PDF), by=person)
    digest = hashlib.sha256(PDF).hexdigest()
    assert stored.sha256 == digest
    assert stored.storage_name == f"{digest[:2]}/{digest[2:4]}/{digest}"
    assert (Path(settings.MEDIA_ROOT) / stored.storage_name).read_bytes() == PDF
    assert stored.size == len(PDF) and stored.content_type == "application/pdf"
    event = events("files.uploaded")[-1]
    assert event.new_value == {
        "nome": "laudo.pdf",
        "tipo": "application/pdf",
        "tamanho": len(PDF),
        "sha256": digest,
    }


@pytest.mark.req("003:FR-020")
def test_mesmo_conteudo_gera_dois_registros_e_um_arquivo(person, settings):
    first = storage.store_upload(upload("a.pdf", PDF), by=person)
    second = storage.store_upload(upload("b.pdf", PDF), by=person)
    assert first.pk != second.pk and first.storage_name == second.storage_name
    files = [path for path in Path(settings.MEDIA_ROOT).rglob("*") if path.is_file()]
    assert len(files) == 1


@pytest.mark.req("003:FR-020")
@pytest.mark.parametrize(
    "name,content",
    [("foto.png", PNG), ("foto.jpg", JPEG), ("foto.jpeg", JPEG), ("certificado.PDF", PDF)],
)
def test_aceita_pdf_png_e_jpeg(person, name, content):
    assert storage.store_upload(upload(name, content), by=person).pk


@pytest.mark.req("003:FR-020")
@pytest.mark.parametrize(
    "name,content",
    [
        ("falso.pdf", b"isto nao e um pdf"),
        ("imagem.png", PDF),
        ("planilha.csv", b"codigo;descricao\n"),
        ("programa.exe", b"MZ" + bytes(10)),
    ],
)
def test_recusa_tipo_pela_assinatura_e_pela_extensao(person, name, content):
    with pytest.raises(ValidationError, match="Tipo de arquivo não aceito"):
        storage.store_upload(upload(name, content), by=person)
    assert not StoredFile.objects.exists()


@pytest.mark.req("003:FR-020")
def test_planilhas_so_quando_permitidas(person):
    stored = storage.store_upload(
        upload("insumos.csv", b"codigo;descricao;tipo\n"),
        by=person,
        allowed=storage.SPREADSHEET_KINDS,
    )
    assert stored.content_type == "text/csv"


@pytest.mark.req("003:FR-020")
def test_recusa_acima_do_tamanho_maximo_e_vazio(person, settings):
    settings.FILE_MAX_MB = 1
    with pytest.raises(ValidationError, match="o máximo é 1 MB"):
        storage.store_upload(upload("grande.pdf", PDF + bytes(1024 * 1024)), by=person)
    with pytest.raises(ValidationError, match="vazio"):
        storage.store_upload(upload("vazio.pdf", b""), by=person)


@pytest.mark.req("003:FR-020")
@pytest.mark.req("003:SC-005")
def test_leitura_confere_o_resumo(person, settings):
    stored = storage.store_upload(upload("laudo.pdf", PDF), by=person)
    assert storage.read_verified(stored) == PDF
    path = Path(settings.MEDIA_ROOT) / stored.storage_name
    path.write_bytes(PDF + b"alterado")
    with pytest.raises(storage.IntegrityFailure) as failure:
        storage.read_verified(stored)
    assert failure.value.actual == hashlib.sha256(PDF + b"alterado").hexdigest()
    path.unlink()
    with pytest.raises(storage.IntegrityFailure) as missing:
        storage.read_verified(stored)
    assert missing.value.actual == "arquivo ausente"


@pytest.mark.req("003:FR-020")
def test_metadados_sao_somente_de_inclusao(person):
    stored = storage.store_upload(upload("laudo.pdf", PDF), by=person)
    with pytest.raises(Exception, match="somente de inclusão"):
        stored.save()
    if not app_role_exists():
        pytest.skip("Papel da aplicação inexistente neste banco.")
    with pytest.raises(ProgrammingError, match="permission denied"):
        run_as_app_role("UPDATE files_storedfile SET sha256 = 'x' WHERE id = %s", [stored.pk])
    with pytest.raises(ProgrammingError, match="permission denied"):
        run_as_app_role("DELETE FROM files_storedfile WHERE id = %s", [stored.pk])
