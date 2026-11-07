"""Código do projeto por sequência anual, sem colisão (FR-015, SC-003 da feature 002)."""

import threading

import pytest
from django.db import connection
from django.test import override_settings

from sgp.accounts.profiles import Profile
from sgp.projects import workflow
from sgp.projects.models import Project

pytestmark = pytest.mark.req("002:FR-015")


@pytest.mark.django_db
def test_sequencia_por_ano_com_tres_digitos():
    assert workflow.next_project_code(2026) == "PD-2026-001"
    assert workflow.next_project_code(2026) == "PD-2026-002"
    assert workflow.next_project_code(2027) == "PD-2027-001"


@pytest.mark.django_db
@override_settings(PROJECT_CODE_PREFIX="PDX")
def test_prefixo_configuravel():
    assert workflow.next_project_code(2030) == "PDX-2030-001"


@pytest.mark.django_db(transaction=True)
@pytest.mark.req("002:SC-003")
def test_aprovacoes_simultaneas_geram_codigos_distintos(make_project, fill_project, make_user):
    managers = [make_user(f"gestor{i}", Profile.RD_MANAGER) for i in range(6)]
    projects = []
    for index in range(6):
        project = fill_project(make_project(title=f"Projeto {index}"))
        workflow.submit(project, by=project.leader)
        projects.append(project)

    errors = []
    barrier = threading.Barrier(len(projects))

    def approve(project, manager):
        try:
            barrier.wait(timeout=10)
            workflow.approve(project, by=manager)
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)
        finally:
            connection.close()

    threads = [
        threading.Thread(target=approve, args=pair) for pair in zip(projects, managers, strict=True)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors
    codes = sorted(Project.objects.values_list("code", flat=True))
    year = codes[0].split("-")[1]
    assert codes == [f"PD-{year}-{n:03d}" for n in range(1, 7)]
