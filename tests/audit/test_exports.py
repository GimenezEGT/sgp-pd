"""Exportação da trilha em CSV e XLSX (FR-024; contrato exportacao-trilha.md)."""

import csv
import io

import pytest
from django.urls import reverse
from openpyxl import load_workbook

from sgp.accounts.profiles import Profile
from sgp.audit.exports import HEADER
from sgp.audit.models import AuditEvent
from sgp.audit.services import record_event

pytestmark = [pytest.mark.django_db, pytest.mark.req("001:FR-024")]


@pytest.fixture
def sample(make_user):
    ana = make_user("ana")
    record_event(
        "audit.exported",
        actor=ana,
        new_value={"formato": "csv"},
        reason="motivo; com ponto e vírgula",
    )
    record_event(
        "accounts.user_updated",
        actor=ana,
        obj=ana,
        old_value={"job_title": "A"},
        new_value={"job_title": "B"},
    )
    record_event("audit.exported", actor=None)
    return ana


def read_csv(response):
    raw = b"".join(response.streaming_content).decode("utf-8")
    assert raw.startswith(chr(0xFEFF))
    return list(csv.reader(io.StringIO(raw[1:]), delimiter=";"))


def test_csv_tem_identificacao_cabecalho_e_eventos_filtrados(client, login_as, sample):
    auditor = login_as(Profile.QUALITY)
    response = client.get(reverse("audit:export"), {"formato": "csv", "usuario": sample.pk})
    assert response["Content-Type"].startswith("text/csv")
    assert 'filename="trilha-auditoria-' in response["Content-Disposition"]
    rows = read_csv(response)
    assert rows[0] == ["Trilha de auditoria — SGP-P&D"]
    assert rows[1][0] == "Exportado em"
    assert rows[2] == ["Exportado por", f"{auditor.username} — {auditor.get_full_name()}"]
    assert rows[3][0] == "Filtros" and "Usuário: ana" in rows[3][1]
    assert rows[4] == ["Eventos", "2"]
    assert rows[5] == []
    assert rows[6] == HEADER
    body = rows[7:]
    assert [row[0] for row in body] == ["1", "2"]
    assert body[0][10] == "motivo; com ponto e vírgula"
    assert body[1][8] == '{"job_title": "A"}' and body[1][9] == '{"job_title": "B"}'


def test_exportacao_gera_evento_com_filtros_e_quantidade(client, login_as, sample):
    auditor = login_as(Profile.QUALITY)
    response = client.get(reverse("audit:export"), {"formato": "csv", "tipo": "audit.exported"})
    rows = read_csv(response)
    event = AuditEvent.objects.filter(event_type="audit.exported", actor=auditor).get()
    assert event.new_value["formato"] == "csv"
    assert event.new_value["filtros"]["tipo"] == "audit.exported"
    assert event.new_value["eventos"] == 2
    # o próprio evento de exportação não entra no arquivo
    assert [row[0] for row in rows[7:]] == ["1", "3"]


def test_xlsx_tem_o_mesmo_conteudo(client, login_as, sample):
    login_as(Profile.RD_MANAGER)
    response = client.get(reverse("audit:export"), {"formato": "xlsx"})
    assert response["Content-Type"].startswith("application/vnd.openxmlformats")
    sheet = load_workbook(io.BytesIO(response.content), read_only=True)["Trilha"]
    rows = [list(row) for row in sheet.iter_rows(values_only=True)]
    assert rows[0][0] == "Trilha de auditoria — SGP-P&D"
    assert rows[4][:2] == ["Eventos", 3]
    assert rows[6] == HEADER
    assert [row[0] for row in rows[7:]] == [1, 2, 3]


def test_exportacao_sem_eventos(client, login_as, sample):
    login_as(Profile.QUALITY)
    rows = read_csv(client.get(reverse("audit:export"), {"formato": "csv", "projeto": 999}))
    assert rows[4] == ["Eventos", "0"]
    assert rows[6] == HEADER and rows[7:] == []


def test_formato_invalido_volta_para_a_trilha(client, login_as, sample):
    auditor = login_as(Profile.QUALITY)
    response = client.get(reverse("audit:export"), {"formato": "pdf"})
    assert response.status_code == 302
    assert not AuditEvent.objects.filter(event_type="audit.exported", actor=auditor).exists()


def test_perfil_sem_permissao_nao_exporta(client, login_as, sample):
    login_as(Profile.ANALYST)
    assert client.get(reverse("audit:export"), {"formato": "csv"}).status_code == 403
