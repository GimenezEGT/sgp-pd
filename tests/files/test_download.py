"""Entrega de arquivos: política do registro dono e recusa de arquivo alterado (FR-020, SC-005)."""

from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from sgp.accounts.profiles import Profile
from sgp.catalog.models import ImportBatch
from sgp.files import storage

pytestmark = [pytest.mark.django_db]

PDF = b"%PDF-1.4\ncertificado ficticio\n%%EOF\n"


@pytest.fixture
def certificate(make_user, make_material):
    owner = make_user(None, Profile.ANALYST)
    stored = storage.store_upload(SimpleUploadedFile("cert.pdf", PDF), by=owner)
    make_material(owner, certificate=stored)
    return stored


@pytest.mark.req("003:FR-020")
def test_certificado_de_insumo_e_entregue_a_qualquer_perfil(client, login_as, certificate):
    login_as(Profile.READER)
    response = client.get(reverse("files:download", args=[certificate.pk]))
    assert response.status_code == 200
    assert response.content == PDF
    assert response["Content-Type"] == "application/pdf"
    assert "attachment" in response["Content-Disposition"]
    assert response["X-Content-Type-Options"] == "nosniff"


@pytest.mark.req("003:FR-020")
@pytest.mark.req("003:SC-005")
def test_arquivo_alterado_nao_e_entregue_e_vai_para_a_trilha(
    client, login_as, certificate, settings, events
):
    (Path(settings.MEDIA_ROOT) / certificate.storage_name).write_bytes(b"%PDF-1.4 adulterado")
    login_as(Profile.ANALYST)
    response = client.get(reverse("files:download", args=[certificate.pk]))
    assert response.status_code == 409
    assert "não será entregue" in response.content.decode()
    event = events("files.integrity_failed")[-1]
    assert event.old_value == {"sha256": certificate.sha256}
    assert event.new_value["sha256"] != certificate.sha256
    assert event.object_id == str(certificate.pk)


@pytest.mark.req("003:FR-020")
def test_arquivo_sem_dono_conhecido_e_negado(client, login_as, make_user, events):
    stored = storage.store_upload(SimpleUploadedFile("solto.pdf", PDF), by=make_user())
    login_as(Profile.QUALITY)
    response = client.get(reverse("files:download", args=[stored.pk]))
    assert response.status_code == 403
    assert events("auth.permission_denied")


@pytest.mark.req("003:FR-020")
@pytest.mark.req("003:FR-008")
def test_planilha_importada_so_para_editores(client, login_as, make_user):
    owner = make_user(None, Profile.ANALYST)
    stored = storage.store_upload(
        SimpleUploadedFile("insumos.csv", b"codigo;descricao;tipo\n"),
        by=owner,
        allowed=storage.SPREADSHEET_KINDS,
    )
    ImportBatch.objects.create(source_file=stored, uploaded_by=owner, rows=[])
    login_as(Profile.READER)
    assert client.get(reverse("files:download", args=[stored.pk])).status_code == 403
    client.logout()
    login_as(Profile.ANALYST)
    assert client.get(reverse("files:download", args=[stored.pk])).status_code == 200
