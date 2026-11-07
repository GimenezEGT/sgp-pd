"""Lista de projetos com filtros (história 5 da feature 002)."""

import time

import pytest
from django.urls import reverse

from sgp.accounts.profiles import Profile
from sgp.projects.models import ProjectStatus

pytestmark = [pytest.mark.django_db, pytest.mark.req("002:FR-018")]


def titles(response):
    return sorted(project.title for project, _ in response.context["rows"])


@pytest.fixture
def portfolio(make_project, make_user, open_project):
    leader_a = make_user("lider.a", Profile.PROJECT_LEADER)
    leader_b = make_user("lider.b", Profile.PROJECT_LEADER)
    make_project(leader=leader_a, title="Alfa", product_name="KIT HEMOGLOBINA")
    make_project(
        leader=leader_b, title="Beta", product_name="KIT GLICOSE", product_family="Família Bio"
    )
    opened = open_project(title="Gama", product_name="KIT PCR")
    return {"a": leader_a, "b": leader_b, "open": opened}


def test_gestor_ve_todos_e_filtra(client, login_as, portfolio):
    login_as(Profile.RD_MANAGER)
    assert titles(client.get(reverse("projects:list"))) == ["Alfa", "Beta", "Gama"]
    assert titles(client.get(reverse("projects:list"), {"status": ProjectStatus.OPEN})) == ["Gama"]
    assert titles(client.get(reverse("projects:list"), {"lider": portfolio["b"].pk})) == ["Beta"]
    assert titles(client.get(reverse("projects:list"), {"produto": "glicose"})) == ["Beta"]
    assert titles(client.get(reverse("projects:list"), {"produto": "família bio"})) == ["Beta"]


def test_lider_ve_so_os_seus(client, portfolio):
    client.force_login(portfolio["a"])
    assert titles(client.get(reverse("projects:list"))) == ["Alfa"]


def test_analista_ve_so_projetos_abertos_de_que_e_membro(client, login_as, portfolio):
    analyst = login_as(Profile.ANALYST)
    assert titles(client.get(reverse("projects:list"))) == []
    portfolio["open"].members.create(
        user=analyst, role="Validação", added_by=portfolio["open"].leader
    )
    assert titles(client.get(reverse("projects:list"))) == ["Gama"]


@pytest.mark.req("002:FR-010")
def test_coluna_de_custo_so_com_permissao(client, login_as, portfolio):
    login_as(Profile.QUALITY)
    page = client.get(reverse("projects:list")).content.decode()
    assert "Custo total" not in page
    client.logout()
    login_as(Profile.RD_MANAGER)
    page = client.get(reverse("projects:list")).content.decode()
    assert "Custo total" in page and "R$ 250.000,00" in page


@pytest.mark.req("002:SC-005")
def test_lista_com_200_projetos_em_menos_de_2_segundos(client, login_as, make_project, make_user):
    leader = make_user("lider.volume", Profile.PROJECT_LEADER)
    for index in range(200):
        make_project(leader=leader, title=f"Projeto {index:03d}")
    login_as(Profile.RD_MANAGER)
    began = time.perf_counter()
    response = client.get(reverse("projects:list"), {"produto": "kit"})
    elapsed = time.perf_counter() - began
    assert response.status_code == 200 and len(response.context["rows"]) == 200
    assert elapsed < 2
