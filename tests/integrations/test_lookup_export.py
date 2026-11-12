"""Consulta de produto, solicitação de insumo novo e exportação de contingência (FR-003, FR-006,
FR-008, SC-003)."""

import csv
import io
import json

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse
from openpyxl import load_workbook

from sgp.integrations import services
from sgp.integrations.models import IntegrationMessage


@pytest.mark.req("012:FR-003")
def test_consulta_de_produto_com_e_sem_erp(client, gateway, configured, member):
    gateway.products["MP-001"] = {
        "CODPROD": "MP-001",
        "DESCRPROD": "Tampão fictício",
        "CODVOL": "L",
        "ATIVO": "S",
    }
    assert services.lookup_product("MP-001") == {
        "codigo": "MP-001",
        "descricao": "Tampão fictício",
        "unidade": "L",
        "situacao": "S",
    }
    with pytest.raises(services.ProductNotFound):
        services.lookup_product("NAO-EXISTE")
    client.force_login(member)
    ok = client.get(reverse("integrations:product"), {"codigo": "MP-001"}).content.decode()
    assert "Tampão fictício" in ok and "unidade L" in ok
    missing = client.get(reverse("integrations:product"), {"codigo": "X-9"}).content.decode()
    assert "não encontrado" in missing


@pytest.mark.req("012:FR-003")
@pytest.mark.req("012:SC-004")
def test_sem_erp_o_cadastro_continua_com_aviso(client, member):
    client.force_login(member)
    page = client.get(reverse("integrations:product"), {"codigo": "MP-001"}).content.decode()
    assert "não conferido" in page and "O cadastro continua normalmente" in page
    form = client.get(reverse("catalog:new", args=["insumos"])).content.decode()
    assert "Consultar no Sankhya" in form


@pytest.mark.req("012:FR-006")
def test_saida_aprovada_gera_solicitacao_de_insumo_novo(
    signed_project, create_sub, force_approve, member, manager
):
    from sgp.audit.services import record_event

    for code in (
        "entrada",
        "formulacao",
        "lote-piloto",
        "rapd",
        "analise-critica",
        "validacao",
        "verificacao-final",
    ):
        force_approve(create_sub(signed_project, code))
    material = _material(member)
    exit_sub = create_sub(signed_project, "saida")
    force_approve(
        exit_sub,
        {
            "novas_materias_primas": {
                "na": False,
                "justification": "",
                "values": {"insumos": [material.pk]},
            }
        },
    )
    record_event(
        "signatures.approved",
        actor=manager,
        object_type="signatures.subdocument",
        object_id=str(exit_sub.pk),
        object_repr=str(exit_sub),
        project_id=signed_project.pk,
    )
    request = IntegrationMessage.objects.get(record_type="insumo_novo")
    assert request.payload["descricao"] == material.description
    assert (
        request.payload["situacao"] == "solicitado"
        and request.payload["codigo_projeto"] == signed_project.code
    )
    assert IntegrationMessage.objects.filter(record_type="documento").exists()


def _material(by):
    from sgp.catalog import versioning
    from sgp.catalog.kinds import MATERIALS

    return versioning.create_record(
        MATERIALS,
        by=by,
        data={
            "code": "MP-NOVA-1",
            "description": "Matéria-prima nova fictícia",
            "material_type": "raw",
            "manufacturer": "Fornecedor fictício",
            "manufacturer_lot": "L123",
            "new_to_company": True,
        },
    )


@pytest.mark.req("012:FR-008")
@pytest.mark.req("012:FR-009")
@pytest.mark.req("012:SC-003")
def test_exportacao_csv_xlsx_json_no_layout_combinado(it_admin, member, signed_project, events):
    assert IntegrationMessage.objects.filter(record_type="projeto").count() == 1
    name, content_type, data = services.export("projeto", "csv", by=it_admin)
    rows = list(csv.reader(io.StringIO(data.decode("utf-8")), delimiter=";"))
    assert name.endswith(".csv") and content_type.startswith("text/csv")
    assert rows[0][:3] == ["chave", "codigo_projeto", "nome"] and rows[1][1] == signed_project.code
    _, _, xlsx = services.export("projeto", "xlsx", by=it_admin)
    sheet = load_workbook(io.BytesIO(xlsx)).active
    assert sheet.cell(2, 2).value == signed_project.code
    _, _, raw = services.export("projeto", "json", by=it_admin)
    envelope = json.loads(raw)
    assert (
        set(envelope) == {"entidade", "gerado_em", "registros"}
        and envelope["entidade"] == "projeto"
    )
    assert envelope["registros"][0]["codigo_projeto"] == signed_project.code
    with pytest.raises(PermissionDenied):
        services.export("projeto", "csv", by=member)
    with pytest.raises(ValidationError):
        services.export("inexistente", "csv", by=it_admin)
    assert len(events("integration.exported")) == 3


@pytest.mark.req("012:FR-002")
def test_mapeamento_validado_e_so_para_a_ti(it_admin, member):
    with pytest.raises(ValidationError, match="chave"):
        services.publish_mapping(by=it_admin, text="registros: {projeto: {entidade: X}}")
    with pytest.raises(ValidationError, match="desconhecidos"):
        services.publish_mapping(by=it_admin, text="registros: {projeto: {campos: {inventado: X}}}")
    with pytest.raises(PermissionDenied):
        services.publish_mapping(by=member, text="registros: {}")
