"""Insumos com certificado de análise (US3: FR-011, FR-012, FR-020 da feature 003)."""

from datetime import date, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from sgp.accounts.profiles import Profile
from sgp.catalog.models import Material

pytestmark = [pytest.mark.django_db]


def material_post(**overrides):
    data = {
        "code": "MP-0100",
        "description": "Tampão Tris 1 M",
        "material_type": "raw",
        "manufacturer": "Fornecedor fictício",
        "manufacturer_lot": "F-77",
        "certificate_valid_until": "",
    }
    data.update(overrides)
    return data


@pytest.fixture
def analyst_client(client, make_user):
    user = make_user(None, Profile.ANALYST)
    client.force_login(user)
    return user


@pytest.mark.req("003:FR-011")
def test_cadastra_insumo_com_certificado(client, analyst_client, pdf_file, events):
    response = client.post(
        reverse("catalog:new", args=["insumos"]),
        material_post(certificate_file=pdf_file(), certificate_valid_until="2027-05-31"),
    )
    material = Material.objects.get()
    assert response.status_code == 302
    assert material.certificate.original_name == "certificado.pdf"
    assert material.certificate_valid_until == date(2027, 5, 31)
    uploaded = events("files.uploaded")[-1]
    created = events("catalog.created")[-1]
    assert uploaded.seq < created.seq
    assert created.new_value["certificate"]["sha256"] == material.certificate.sha256


@pytest.mark.req("003:FR-011")
def test_validade_obrigatoria_quando_ha_certificado(client, analyst_client, pdf_file):
    response = client.post(
        reverse("catalog:new", args=["insumos"]), material_post(certificate_file=pdf_file())
    )
    assert "Informe a validade do certificado de análise." in response.content.decode()
    assert not Material.objects.exists()


@pytest.mark.req("003:FR-020")
def test_certificado_em_formato_nao_aceito_e_recusado(client, analyst_client, pdf_file):
    response = client.post(
        reverse("catalog:new", args=["insumos"]),
        material_post(
            certificate_file=pdf_file("certificado.docx", b"PK conteudo"),
            certificate_valid_until="2027-01-01",
        ),
    )
    assert "Tipo de arquivo não aceito" in response.content.decode()
    assert not Material.objects.exists()


@pytest.mark.req("003:FR-011")
def test_codigo_de_insumo_repetido_e_recusado(client, analyst_client, make_material):
    make_material(analyst_client, code="MP-0100")
    response = client.post(reverse("catalog:new", args=["insumos"]), material_post())
    assert "Já existe insumo vigente com código MP-0100." in response.content.decode()
    assert Material.objects.count() == 1


@pytest.mark.req("003:FR-011")
def test_codigo_com_espaco_e_recusado(client, analyst_client):
    response = client.post(reverse("catalog:new", args=["insumos"]), material_post(code="MP 01"))
    assert "não pode ter espaços" in response.content.decode()


@pytest.mark.req("003:FR-012")
def test_certificado_vencido_gera_alerta_sem_bloquear(
    client, analyst_client, make_material, pdf_file
):
    from sgp.files.storage import store_upload

    expired = timezone.localdate() - timedelta(days=1)
    material = make_material(
        analyst_client,
        code="MP-VENC",
        certificate=store_upload(pdf_file(), by=analyst_client),
        certificate_valid_until=expired,
    )
    assert material.certificate_expired
    detail = client.get(reverse("catalog:detail", args=["insumos", material.pk])).content.decode()
    assert "Certificado vencido" in detail
    fragment = client.get(
        reverse("catalog:search", args=["insumos"]), {"q": "VENC"}
    ).content.decode()
    assert "MP-VENC" in fragment and "Certificado vencido" in fragment
    listing = client.get(reverse("catalog:list", args=["insumos"])).content.decode()
    assert "Certificado vencido" in listing


@pytest.mark.req("003:FR-012")
def test_insumo_sem_certificado_mostra_pendencia(client, analyst_client, make_material):
    material = make_material(analyst_client)
    assert material.certificate_pending and not material.certificate_expired
    detail = client.get(reverse("catalog:detail", args=["insumos", material.pk])).content.decode()
    assert "Certificado pendente" in detail


@pytest.mark.req("003:FR-011")
def test_novo_certificado_numa_correcao(client, analyst_client, make_material, pdf_file):
    material = make_material(analyst_client)
    response = client.post(
        reverse("catalog:edit", args=["insumos", material.pk]),
        material_post(
            code=material.code,
            certificate_file=pdf_file("novo.pdf"),
            certificate_valid_until="2028-01-31",
            new_to_company="on",
            row_version=material.row_version,
        ),
    )
    assert response.status_code == 302
    material.refresh_from_db()
    assert material.certificate.original_name == "novo.pdf"
    assert material.new_to_company is True


@pytest.mark.req("003:FR-020")
def test_detalhe_traz_o_link_conferido_do_certificado(
    client, analyst_client, make_material, pdf_file
):
    from sgp.files.storage import store_upload

    stored = store_upload(pdf_file(), by=analyst_client)
    material = make_material(
        analyst_client, certificate=stored, certificate_valid_until=date(2030, 1, 1)
    )
    detail = client.get(reverse("catalog:detail", args=["insumos", material.pk])).content.decode()
    assert reverse("files:download", args=[stored.pk]) in detail
    assert stored.sha256 in detail
