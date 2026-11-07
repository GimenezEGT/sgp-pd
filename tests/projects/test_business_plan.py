"""Plano de Negócios e proteção dos dados financeiros (história 3 da feature 002)."""

import csv
import io
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from sgp.accounts.profiles import Profile
from sgp.audit.masking import MASK
from sgp.audit.models import AuditEvent
from sgp.projects import services

pytestmark = pytest.mark.django_db


def plan_post(**overrides):
    data = {
        "plan_date": "2026-11-07",
        "objective": "Objetivo",
        "description": "Descrição",
        "total_cost": "1.234.567,89",
        "execution_months": "18",
        "target_market": "Laboratórios",
        "competitors": "Concorrente A",
        "competitor_price_min": "8,50",
        "competitor_price_max": "12,00",
        "competitor_presentations": "96 testes",
        "max_production_cost": "4,20",
        "sale_price_min": "9,00",
        "sale_price_max": "11,00",
        "annual_sales_tests": "120000",
        "factory_structure": "Adequada",
        "production_team": "Treinada",
        "quality_control": "Ok",
        "forecast_1": "100.000,00",
        "forecast_2": "200.000,00",
        "forecast_3": "300.000,00",
        "forecast_4": "400.000,00",
        "forecast_5": "500.000,00",
        "row_version": "0",
    }
    data.update(overrides)
    return data


@pytest.mark.req("002:FR-007")
@pytest.mark.req("002:FR-008")
@pytest.mark.req("002:FR-009")
def test_plano_salvo_com_total_calculado(client, make_project):
    project = make_project()
    client.force_login(project.leader)
    response = client.post(reverse("projects:business_plan", args=[project.pk]), plan_post())
    assert response.status_code == 302
    plan = project.business_plan
    plan.refresh_from_db()
    assert plan.total_cost == Decimal("1234567.89")
    assert plan.forecast_total == Decimal("1500000.00")
    page = client.get(reverse("projects:detail", args=[project.pk])).content.decode()
    assert "R$ 1.234.567,89" in page and "R$ 1.500.000,00" in page
    assert (
        "forecast_total"
        not in client.get(reverse("projects:business_plan", args=[project.pk])).content.decode()
    )


@pytest.mark.req("002:FR-008")
def test_total_considera_so_anos_preenchidos(make_project):
    project = make_project()
    services.update_business_plan(
        project, by=project.leader, data={}, forecasts={1: Decimal("10.00"), 3: Decimal("5.50")}
    )
    assert project.business_plan.forecast_total == Decimal("15.50")


@pytest.mark.req("002:FR-009")
@pytest.mark.parametrize(
    "field,value",
    [
        ("total_cost", "-1,00"),
        ("sale_price_min", "20,00"),
        ("forecast_1", "10,999"),
        ("annual_sales_tests", "-5"),
    ],
)
def test_valores_invalidos_sao_recusados(client, make_project, field, value):
    project = make_project()
    client.force_login(project.leader)
    response = client.post(
        reverse("projects:business_plan", args=[project.pk]), plan_post(**{field: value})
    )
    assert response.status_code == 200
    project.business_plan.refresh_from_db()
    assert project.business_plan.total_cost is None


def test_faixa_invalida_tambem_e_recusada_no_servico(make_project):
    project = make_project()
    with pytest.raises(ValidationError, match="mínimo não pode ser maior"):
        services.update_business_plan(
            project,
            by=project.leader,
            data={"competitor_price_min": Decimal("10"), "competitor_price_max": Decimal("5")},
            forecasts={},
        )


@pytest.fixture
def project_with_plan(make_project, fill_project):
    return fill_project(make_project(), total_cost=Decimal("987654.32"))


FINANCIAL_STRINGS = ["987.654,32", "1.500.000,00", "8,50", "4,20", "120.000"]


@pytest.mark.req("002:FR-010")
@pytest.mark.req("002:SC-002")
@pytest.mark.parametrize("profile", [Profile.QUALITY, Profile.ADMIN])
def test_perfil_global_sem_permissao_ve_restrito(client, login_as, project_with_plan, profile):
    login_as(profile)
    page = client.get(reverse("projects:detail", args=[project_with_plan.pk])).content.decode()
    assert "Restrito" in page
    for text in FINANCIAL_STRINGS:
        assert text not in page, text
    assert "Concorrente A" in page


@pytest.mark.req("002:FR-010")
@pytest.mark.req("002:SC-002")
def test_url_direta_da_edicao_e_negada(client, login_as, project_with_plan):
    user = login_as(Profile.QUALITY)
    response = client.get(reverse("projects:business_plan", args=[project_with_plan.pk]))
    assert response.status_code == 403
    for text in FINANCIAL_STRINGS:
        assert text not in response.content.decode()
    assert AuditEvent.objects.filter(event_type="auth.permission_denied", actor=user).exists()


@pytest.mark.req("002:FR-010")
def test_gestor_ve_os_dados_financeiros(client, login_as, project_with_plan):
    login_as(Profile.RD_MANAGER)
    page = client.get(reverse("projects:detail", args=[project_with_plan.pk])).content.decode()
    assert "R$ 987.654,32" in page and "R$ 1.500.000,00" in page


@pytest.mark.req("002:FR-010")
@pytest.mark.req("002:SC-002")
def test_trilha_e_exportacao_mascaram_financeiros(client, login_as, project_with_plan):
    login_as(Profile.QUALITY)
    page = client.get(
        reverse("audit:trail"), {"tipo": "projects.business_plan_updated"}
    ).content.decode()
    assert MASK in page
    assert "987654.32" not in page
    response = client.get(
        reverse("audit:export"), {"tipo": "projects.business_plan_updated", "formato": "csv"}
    )
    raw = b"".join(response.streaming_content).decode("utf-8")
    rows = list(csv.reader(io.StringIO(raw[1:]), delimiter=";"))
    assert MASK in rows[7][9] and "987654.32" not in raw
    assert "Kit para extração" in raw


@pytest.mark.req("002:FR-010")
def test_trilha_mostra_valores_ao_gestor(client, login_as, project_with_plan):
    login_as(Profile.RD_MANAGER)
    page = client.get(
        reverse("audit:trail"), {"tipo": "projects.business_plan_updated"}
    ).content.decode()
    assert "987654.32" in page


@pytest.mark.req("002:FR-007")
def test_nome_e_lider_vem_do_projeto(client, make_project):
    project = make_project(title="Projeto Bio Gene")
    client.force_login(project.leader)
    page = client.get(reverse("projects:business_plan", args=[project.pk])).content.decode()
    assert "Projeto Bio Gene" in page and project.leader.get_full_name() in page
    assert 'name="title"' not in page


@pytest.mark.req("002:FR-020")
def test_plano_gravado_por_outra_pessoa_antes_e_recusado(make_project):
    project = make_project()
    services.update_business_plan(
        project, by=project.leader, data={"objective": "A"}, forecasts={}, row_version=0
    )
    with pytest.raises(ValidationError, match="Outra pessoa gravou"):
        services.update_business_plan(
            project, by=project.leader, data={"objective": "B"}, forecasts={}, row_version=0
        )
