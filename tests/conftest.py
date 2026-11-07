"""Fixtures comuns e plugin de rastreabilidade requisito → teste (princípio VIII)."""

import json
import re
from pathlib import Path

import pytest
from django.core.management import call_command

from tests import fake_backend

REQ_PATTERN = re.compile(r"^\d{3}:(FR|SC)-\d{3}$")


def pytest_addoption(parser):
    parser.addoption(
        "--req-report",
        action="store",
        default=None,
        help="grava em JSON o mapa teste → requisitos (matriz de rastreabilidade)",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    report = {}
    for item in items:
        ids = []
        for marker in item.iter_markers("req"):
            for value in marker.args:
                if not REQ_PATTERN.match(value):
                    raise pytest.UsageError(f"Requisito inválido em {item.nodeid}: {value!r}")
                ids.append(value)
        report[item.nodeid] = sorted(set(ids))
    path = config.getoption("--req-report")
    if path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("apply_db_privileges", "--if-role-exists", verbosity=0)


@pytest.fixture(autouse=True)
def _reset_directory():
    fake_backend.reset()
    yield
    fake_backend.reset()


@pytest.fixture
def directory():
    return fake_backend


@pytest.fixture
def make_user(db):
    from sgp.accounts.models import ProfileAssignment, User

    counter = {"value": 0}

    def _make(username=None, *profiles, **attrs):
        counter["value"] += 1
        username = username or f"pessoa{counter['value']}"
        attrs.setdefault("full_name", f"Pessoa {username}")
        attrs.setdefault("job_title", "Analista de P&D")
        user = User.objects.create_user(username, **attrs)
        for profile in profiles:
            ProfileAssignment.objects.create(
                user=user,
                profile=profile,
                grant_reason="Preparação do teste",
                approval_reference="teste automatizado",
            )
        return user

    return _make


@pytest.fixture
def login_as(client, make_user):
    def _login(*profiles, username=None):
        user = make_user(username, *profiles)
        client.force_login(user)
        return user

    return _login


@pytest.fixture
def events():
    """Consulta rápida de eventos por tipo."""
    from sgp.audit.models import AuditEvent

    def _events(event_type=None):
        queryset = AuditEvent.objects.order_by("seq")
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        return list(queryset)

    return _events


PLAN_COMPLETE = {
    "objective": "Desenvolver kit de extração",
    "description": "Kit para extração de ácidos nucleicos",
    "target_market": "Laboratórios clínicos",
    "execution_months": 18,
    "competitors": ["Concorrente A", "Concorrente B"],
    "competitor_presentations": ["96 testes", "48 testes"],
    "factory_structure": "Adequada",
    "production_team": "Treinada",
    "quality_control": "Métodos disponíveis",
}


@pytest.fixture
def vocab_seed(db):
    """Garante a carga inicial das listas (testes transacionais esvaziam o banco)."""
    from django.apps import apps as django_apps

    from sgp.vocab.seed import SEED, load

    load(django_apps, SEED)


@pytest.fixture
def make_project(make_user, vocab_seed):
    from sgp.accounts.profiles import Profile
    from sgp.projects import services
    from sgp.vocab.models import TECHNOLOGY, get_term

    def _make(leader=None, **data):
        leader = leader or make_user(None, Profile.PROJECT_LEADER)
        values = {
            "title": "Projeto de teste",
            "product_name": "KIT DE TESTE",
            "product_family": "",
            "technology": get_term(TECHNOLOGY, "biologia-molecular"),
            "regulatory_body": "ANVISA",
            "risk_class": "II",
            "classification_rule": "Regra 5, item d",
        }
        values.update(data)
        return services.create_project(by=leader, data=values)

    return _make


@pytest.fixture
def fill_project():
    """Preenche TAP, marco e Plano de Negócios até não restar pendência."""
    from datetime import date
    from decimal import Decimal

    from sgp.projects import services
    from sgp.vocab.models import SUBDOCUMENT_TYPE, get_term

    def _fill(project, total_cost=Decimal("250000.00")):
        leader = project.leader
        services.update_charter(
            project,
            by=leader,
            data={
                "justification": "Demanda de mercado",
                "objective": "Lançar o kit",
                "scope_included": ["Formulação"],
                "deliverables": ["Kit validado"],
                "risks": [{"risco": "Atraso", "impacto": "Prazo", "resposta": "Plano B"}],
                "stakeholders": [{"nome_area": "Comercial", "interesse": "Lançamento"}],
            },
        )
        services.add_milestone(
            project,
            by=leader,
            subdocument_type=get_term(SUBDOCUMENT_TYPE, "entrada"),
            planned_date=date(2026, 12, 15),
        )
        services.update_business_plan(
            project,
            by=leader,
            data={
                **PLAN_COMPLETE,
                "plan_date": date(2026, 11, 7),
                "total_cost": total_cost,
                "competitor_price_min": Decimal("8.50"),
                "competitor_price_max": Decimal("12.00"),
                "max_production_cost": Decimal("4.20"),
                "sale_price_min": Decimal("9.00"),
                "sale_price_max": Decimal("11.00"),
                "annual_sales_tests": 120000,
            },
            forecasts={year: Decimal("100000.00") * year for year in range(1, 6)},
        )
        project.refresh_from_db()
        return project

    return _fill


@pytest.fixture
def open_project(make_project, fill_project, make_user):
    """Projeto aberto (aprovado) com um Gestor de P&D diferente do líder."""
    from sgp.accounts.profiles import Profile
    from sgp.projects import workflow

    def _open(**data):
        project = fill_project(make_project(**data))
        workflow.submit(project, by=project.leader)
        manager = make_user(None, Profile.RD_MANAGER)
        return workflow.approve(project, by=manager)

    return _open


@pytest.fixture
def bare_project(make_user, vocab_seed):
    """Projeto gravado direto (sem eventos), para testes que só precisam do identificador."""
    from sgp.accounts.profiles import Profile
    from sgp.projects.models import Project
    from sgp.vocab.models import TECHNOLOGY, get_term

    def _bare(title="Projeto avulso"):
        leader = make_user(None, Profile.PROJECT_LEADER)
        return Project.objects.create(
            title=title,
            product_name="KIT",
            technology=get_term(TECHNOLOGY, "outras"),
            regulatory_body="ANVISA",
            leader=leader,
            created_by=leader,
        )

    return _bare
