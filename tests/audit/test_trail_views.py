"""Consulta filtrada da trilha (FR-023, FR-025)."""

from datetime import UTC, datetime

import pytest
from django.urls import reverse

from sgp.accounts.profiles import Profile
from sgp.audit.models import AuditEvent
from sgp.audit.services import record_event
from tests.db_helpers import tamper

pytestmark = [pytest.mark.django_db, pytest.mark.req("001:FR-023")]


@pytest.fixture
def sample(make_user):
    ana = make_user("ana")
    bruno = make_user("bruno")
    record_event("audit.exported", actor=ana, new_value={"n": 1})
    record_event("accounts.user_updated", actor=bruno, obj=bruno, project_id=10)
    record_event("audit.exported", actor=bruno, project_id=11)
    record_event("accounts.user_updated", actor=ana, obj=ana, project_id=10)
    return {"ana": ana, "bruno": bruno}


def seqs(response):
    return [event.seq for event in response.context["page"].object_list]


@pytest.mark.parametrize("profile", [Profile.QUALITY, Profile.RD_MANAGER, Profile.ADMIN])
def test_perfis_autorizados_consultam(client, login_as, sample, profile):
    login_as(profile)
    response = client.get(reverse("audit:trail"))
    assert response.status_code == 200
    assert seqs(response) == [1, 2, 3, 4]


@pytest.mark.parametrize("profile", [Profile.ANALYST, Profile.PROJECT_LEADER, Profile.READER])
def test_demais_perfis_recebem_403_e_tentativa_e_registrada(client, login_as, sample, profile):
    user = login_as(profile)
    assert client.get(reverse("audit:trail")).status_code == 403
    denied = AuditEvent.objects.filter(event_type="auth.permission_denied", actor=user).get()
    assert denied.new_value["rota"] == reverse("audit:trail")


def test_filtro_por_usuario(client, login_as, sample):
    login_as(Profile.QUALITY)
    response = client.get(reverse("audit:trail"), {"usuario": sample["ana"].pk})
    assert seqs(response) == [1, 4]


def test_filtro_por_tipo(client, login_as, sample):
    login_as(Profile.QUALITY)
    response = client.get(reverse("audit:trail"), {"tipo": "accounts.user_updated"})
    assert seqs(response) == [2, 4]


def test_filtro_por_projeto(client, login_as, sample):
    login_as(Profile.QUALITY)
    response = client.get(reverse("audit:trail"), {"projeto": 10})
    assert seqs(response) == [2, 4]


def test_filtros_combinados(client, login_as, sample):
    login_as(Profile.QUALITY)
    response = client.get(
        reverse("audit:trail"),
        {"usuario": sample["bruno"].pk, "tipo": "audit.exported", "projeto": 11},
    )
    assert seqs(response) == [3]


def test_filtro_por_periodo_em_horario_de_brasilia(client, login_as):
    record_event("audit.exported", actor=None)  # seq 1
    record_event("audit.exported", actor=None)  # seq 2
    # 06/11 23:30 em Brasília = 07/11 02:30 UTC; 07/11 00:30 em Brasília = 07/11 03:30 UTC
    tamper(
        "UPDATE audit_auditevent SET occurred_at = %s WHERE seq = 1",
        [datetime(2026, 11, 7, 2, 30, tzinfo=UTC)],
    )
    tamper(
        "UPDATE audit_auditevent SET occurred_at = %s WHERE seq = 2",
        [datetime(2026, 11, 7, 3, 30, tzinfo=UTC)],
    )
    login_as(Profile.QUALITY)
    response = client.get(reverse("audit:trail"), {"de": "2026-11-07", "ate": "2026-11-07"})
    assert seqs(response) == [2]
    response = client.get(reverse("audit:trail"), {"ate": "2026-11-06"})
    assert seqs(response) == [1]


def test_periodo_invalido_nao_traz_eventos(client, login_as, sample):
    login_as(Profile.QUALITY)
    response = client.get(reverse("audit:trail"), {"de": "2026-11-08", "ate": "2026-11-01"})
    assert seqs(response) == []
    assert "A data inicial não pode ser posterior à final." in response.content.decode()


def test_paginacao_de_50_em_ordem_cronologica(client, login_as):
    for index in range(55):
        record_event("audit.exported", actor=None, new_value={"i": index})
    login_as(Profile.QUALITY)
    first = client.get(reverse("audit:trail"))
    assert seqs(first) == list(range(1, 51))
    second = client.get(reverse("audit:trail"), {"pagina": 2})
    assert seqs(second)[:5] == [51, 52, 53, 54, 55]


def test_requisicao_htmx_recebe_so_a_tabela(client, login_as, sample):
    login_as(Profile.QUALITY)
    response = client.get(reverse("audit:trail"), HTTP_HX_REQUEST="true")
    content = response.content.decode()
    assert "<html" not in content
    assert "Exportar CSV" in content


@pytest.mark.req("001:FR-025")
def test_data_e_hora_exibidas_em_brasilia_com_segundos(client, login_as):
    record_event("audit.exported", actor=None)
    tamper(
        "UPDATE audit_auditevent SET occurred_at = %s WHERE seq = 1",
        [datetime(2026, 11, 7, 13, 5, 22, tzinfo=UTC)],
    )
    login_as(Profile.QUALITY)
    content = client.get(reverse("audit:trail")).content.decode()
    assert "07/11/2026 10:05:22" in content
