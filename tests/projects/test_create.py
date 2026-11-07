"""Criação do projeto em rascunho (história 1 da feature 002)."""

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from sgp.accounts.profiles import Profile
from sgp.audit.models import AuditEvent
from sgp.projects import services
from sgp.projects.models import Project, ProjectStatus
from sgp.vocab.models import TECHNOLOGY, get_term

pytestmark = pytest.mark.django_db


def form_data(**overrides):
    data = {
        "title": "Extração magnética",
        "product_name": "KIT EXTRAÇÃO MAGNÉTICA",
        "product_family": "",
        "technology": get_term(TECHNOLOGY, "biologia-molecular").pk,
        "regulatory_body": "ANVISA",
        "risk_class": "II",
        "classification_rule": "Regra 5, item d",
    }
    data.update(overrides)
    return data


@pytest.mark.req("002:FR-001")
def test_lider_cria_rascunho_e_evento(client, login_as):
    leader = login_as(Profile.PROJECT_LEADER)
    response = client.post(reverse("projects:new"), form_data())
    project = Project.objects.get()
    assert response["Location"] == reverse("projects:detail", args=[project.pk])
    assert (
        project.status == ProjectStatus.DRAFT and project.code is None and project.version is None
    )
    assert project.leader == leader
    assert project.members.get().user == leader
    assert project.business_plan.forecasts.count() == 5
    event = AuditEvent.objects.get(event_type="projects.created")
    assert event.project_id == project.pk and event.new_value["technology"] == "Biologia molecular"


@pytest.mark.req("002:FR-002")
@pytest.mark.parametrize(
    "risk_class,regime",
    [("I", "Notificação"), ("II", "Notificação"), ("III", "Registro"), ("IV", "Registro")],
)
def test_regime_deduzido_da_classe(make_project, risk_class, regime):
    assert make_project(risk_class=risk_class).regime == regime


@pytest.mark.req("002:FR-002")
def test_projeto_mapa_dispensa_classe(make_project):
    project = make_project(regulatory_body="MAPA", risk_class="III", classification_rule="Regra X")
    assert project.risk_class == "" and project.classification_rule == "" and project.regime == ""


@pytest.mark.req("002:FR-003")
def test_analista_nao_abre_rascunho(client, login_as, make_project):
    project = make_project()
    analyst = login_as(Profile.ANALYST)
    assert client.get(reverse("projects:detail", args=[project.pk])).status_code == 403
    assert AuditEvent.objects.filter(event_type="auth.permission_denied", actor=analyst).exists()


@pytest.mark.req("002:FR-001")
@pytest.mark.parametrize(
    "profile", [Profile.ANALYST, Profile.QUALITY, Profile.READER, Profile.ADMIN]
)
def test_sem_perfil_de_criacao_nao_cria(client, login_as, profile):
    login_as(profile)
    assert client.post(reverse("projects:new"), form_data()).status_code == 403
    assert not Project.objects.exists()


@pytest.mark.req("002:FR-001")
def test_gestor_cria_indicando_lider(client, login_as, make_user):
    login_as(Profile.RD_MANAGER)
    leader = make_user("lider", Profile.PROJECT_LEADER)
    client.post(reverse("projects:new"), form_data(leader=leader.pk))
    assert Project.objects.get().leader == leader


def test_lider_indicado_precisa_do_perfil(make_user):
    manager = make_user(None, Profile.RD_MANAGER)
    with pytest.raises(ValidationError):
        services.create_project(by=manager, data={}, leader=make_user(None, Profile.ANALYST))


@pytest.mark.req("002:FR-019")
def test_edicao_do_produto_gera_evento_com_valores(client, make_project):
    project = make_project()
    client.force_login(project.leader)
    client.post(
        reverse("projects:edit", args=[project.pk]),
        form_data(title="Projeto de teste", product_name="NOVO NOME", row_version=0),
    )
    event = AuditEvent.objects.get(event_type="projects.updated")
    assert event.old_value == {"product_name": "KIT DE TESTE"} and event.new_value == {
        "product_name": "NOVO NOME"
    }
    assert event.project_id == project.pk


@pytest.mark.req("002:FR-020")
def test_edicao_com_versao_desatualizada_e_recusada(make_project):
    project = make_project()
    services.update_product(project, by=project.leader, data={"title": "A"}, row_version=0)
    with pytest.raises(ValidationError, match="Outra pessoa gravou"):
        services.update_product(project, by=project.leader, data={"title": "B"}, row_version=0)
