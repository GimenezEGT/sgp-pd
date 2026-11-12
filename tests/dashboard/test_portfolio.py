"""Carteira de projetos, totais, permissões, cache e desempenho (FR-001, FR-002, FR-004, SC-001)."""

import time
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from sgp.dashboard import portfolio
from sgp.projects.models import Milestone
from sgp.vocab.models import SUBDOCUMENT_TYPE, get_term


def _row(user, project):
    return next(row for row in portfolio.project_rows(user) if row["id"] == project.pk)


@pytest.mark.req("010:FR-001")
def test_indicadores_por_projeto(project, analyst, manager, make_subdocument, approve_quick):
    approve_quick(make_subdocument(project, "entrada"))
    Milestone.objects.create(
        project=project,
        subdocument_type=get_term(SUBDOCUMENT_TYPE, "formulacao"),
        planned_date=timezone.localdate() - timedelta(days=9),
        created_by=project.leader,
    )
    Milestone.objects.create(
        project=project,
        subdocument_type=get_term(SUBDOCUMENT_TYPE, "lote-piloto"),
        planned_date=timezone.localdate() - timedelta(days=20),
        actual_date=timezone.localdate() - timedelta(days=15),
        created_by=project.leader,
    )
    row = _row(manager, project)
    assert row["stage"] == get_term(SUBDOCUMENT_TYPE, "formulacao").label
    assert (row["approved"], row["percent"]) == (1, 12)
    assert (row["milestones_planned"], row["milestones_done"]) == (3, 1)
    assert row["delay"] == 9
    assert row["leader"] == (project.leader.get_full_name() or project.leader.username)


@pytest.mark.req("010:FR-001")
def test_regra_unica_de_acesso(project, analyst, make_user):
    from sgp.accounts.profiles import Profile

    outsider = make_user(None, Profile.ANALYST)
    assert portfolio.project_rows(outsider) == []
    assert [row["id"] for row in portfolio.project_rows(analyst)] == [project.pk]


@pytest.mark.req("010:FR-002")
@pytest.mark.req("010:SC-003")
def test_custo_e_retorno_so_com_permissao(client, project, analyst, manager):
    assert _row(manager, project)["cost"] == "R$ 250.000,00"
    assert _row(manager, project)["return"] == "R$ 1.500.000,00"
    member_row = _row(analyst, project)
    assert not member_row["financial"] and member_row["cost"] == "" and member_row["return"] == ""
    client.force_login(analyst)
    page = client.get(reverse("dashboard:portfolio")).content.decode()
    assert "Custo planejado" not in page and "250.000,00" not in page
    client.force_login(manager)
    page = client.get(reverse("dashboard:portfolio")).content.decode()
    assert "Custo planejado" in page and "250.000,00" in page


@pytest.mark.req("010:FR-004")
def test_totais_com_a_fila_do_gestor(project, analyst, manager, submitted_entry):
    data = portfolio.portfolio(manager, refresh=True)
    totals = data["totals"]
    assert totals["approver"] and totals["waiting"] == 1 and totals["longest_wait"] == 0
    assert totals["open"] >= 1
    assert portfolio.portfolio(analyst, refresh=True)["totals"]["approver"] is False


@pytest.mark.req("010:FR-001")
def test_cache_de_cinco_minutos(project, manager, make_subdocument, approve_quick):
    first = portfolio.portfolio(manager)
    approve_quick(make_subdocument(project, "entrada"))
    cached = portfolio.portfolio(manager)
    assert cached["built_at"] == first["built_at"]
    fresh = portfolio.portfolio(manager, refresh=True)
    assert next(row for row in fresh["rows"] if row["id"] == project.pk)["approved"] == 1


@pytest.mark.req("010:SC-001")
def test_cem_projetos_em_menos_de_dois_segundos(bare_project, manager):
    projects = [bare_project(title=f"Projeto {n}") for n in range(100)]
    term = get_term(SUBDOCUMENT_TYPE, "entrada")
    Milestone.objects.bulk_create(
        Milestone(
            project=p,
            subdocument_type=term,
            planned_date=timezone.localdate() - timedelta(days=n % 10),
            created_by=p.leader,
        )
        for n, p in enumerate(projects)
    )
    start = time.perf_counter()
    data = portfolio.portfolio(manager, refresh=True)
    elapsed = time.perf_counter() - start
    assert len(data["rows"]) >= 100
    assert elapsed < 2, elapsed
