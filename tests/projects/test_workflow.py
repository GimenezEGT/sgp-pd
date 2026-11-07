"""Máquina de estados: submeter, devolver e aprovar (história 4 da feature 002)."""

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from sgp.accounts.profiles import Profile
from sgp.audit.models import AuditEvent
from sgp.core.access import can_access_project
from sgp.projects import workflow
from sgp.projects.models import DecisionAction, ProjectStatus

pytestmark = pytest.mark.django_db


@pytest.fixture
def manager(make_user):
    return make_user("gestor", Profile.RD_MANAGER)


@pytest.mark.req("002:FR-011")
@pytest.mark.parametrize(
    "action,status",
    [
        ("approve", "draft"),
        ("return", "draft"),
        ("submit", "submitted"),
        ("approve", "returned"),
        ("submit", "open"),
        ("return", "open"),
        ("approve", "open"),
    ],
)
def test_transicoes_invalidas_sao_recusadas(action, status):
    with pytest.raises(ValidationError):
        workflow.target_status(action, status)


@pytest.mark.req("002:FR-011")
def test_transicoes_validas():
    assert workflow.target_status("submit", "draft") == ProjectStatus.SUBMITTED
    assert workflow.target_status("submit", "returned") == ProjectStatus.SUBMITTED
    assert workflow.target_status("approve", "submitted") == ProjectStatus.OPEN
    assert workflow.target_status("return", "submitted") == ProjectStatus.RETURNED


@pytest.mark.req("002:FR-012")
def test_submissao_com_pendencias_e_recusada_e_lista_o_que_falta(client, make_project):
    project = make_project()
    client.force_login(project.leader)
    page = client.get(reverse("projects:detail", args=[project.pk])).content.decode()
    assert "Pendências para submeter" in page and "TAP: informe a justificativa." in page
    response = client.post(reverse("projects:submit", args=[project.pk]), follow=True)
    project.refresh_from_db()
    assert project.status == ProjectStatus.DRAFT
    assert "Plano de Negócios: informe o custo total." in response.content.decode()


@pytest.mark.req("002:FR-012")
def test_pendencia_de_classe_so_em_anvisa(make_project, fill_project):
    from sgp.projects.completeness import pending_items

    anvisa = fill_project(make_project(risk_class="", classification_rule=""))
    assert "Produto: informe a classe de risco prevista." in pending_items(anvisa)
    mapa = fill_project(make_project(regulatory_body="MAPA"))
    assert pending_items(mapa) == []


@pytest.mark.req("002:FR-012")
@pytest.mark.req("002:FR-016")
@pytest.mark.req("002:SC-001")
def test_fluxo_completo_com_devolucao_e_aprovacao(
    client, make_project, fill_project, manager, make_user
):
    project = fill_project(make_project())
    analyst = make_user("ana", Profile.ANALYST)
    project.members.create(user=analyst, role="Formulação", added_by=project.leader)
    client.force_login(project.leader)
    client.post(reverse("projects:submit", args=[project.pk]))
    project.refresh_from_db()
    assert project.status == ProjectStatus.SUBMITTED

    client.force_login(manager)
    client.post(reverse("projects:return", args=[project.pk]), {"comment": ""})
    project.refresh_from_db()
    assert project.status == ProjectStatus.SUBMITTED
    client.post(reverse("projects:return", args=[project.pk]), {"comment": "Detalhar riscos"})
    project.refresh_from_db()
    assert project.status == ProjectStatus.RETURNED

    client.force_login(project.leader)
    client.post(reverse("projects:submit", args=[project.pk]))
    client.force_login(manager)
    assert not can_access_project(analyst, project)
    client.post(reverse("projects:approve", args=[project.pk]))
    project.refresh_from_db()
    assert project.status == ProjectStatus.OPEN and project.version_display == "01"
    assert project.code.startswith("PD-") and project.approved_by == manager
    assert can_access_project(analyst, project)

    actions = list(project.decisions.values_list("action", "comment"))
    assert actions == [
        (DecisionAction.SUBMITTED, ""),
        (DecisionAction.RETURNED, "Detalhar riscos"),
        (DecisionAction.SUBMITTED, ""),
        (DecisionAction.APPROVED, ""),
    ]
    approved = AuditEvent.objects.get(event_type="projects.approved")
    assert approved.new_value == {"situacao": "open", "codigo": project.code, "versao": "01"}
    returned = AuditEvent.objects.get(event_type="projects.returned")
    assert returned.reason == "Detalhar riscos"


@pytest.mark.req("002:FR-014")
def test_somente_gestor_decide_e_nao_o_lider(make_project, fill_project, make_user):
    leader = make_user("lider.gestor", Profile.PROJECT_LEADER, Profile.RD_MANAGER)
    project = fill_project(make_project(leader=leader))
    workflow.submit(project, by=leader)
    with pytest.raises(ValidationError, match="próprio projeto"):
        workflow.approve(project, by=leader)
    with pytest.raises(ValidationError, match="Só o Gestor"):
        workflow.approve(project, by=make_user(None, Profile.QUALITY))


@pytest.mark.req("002:FR-014")
@pytest.mark.parametrize("profile", [Profile.PROJECT_LEADER, Profile.QUALITY, Profile.ADMIN])
def test_outros_perfis_recebem_403_ao_aprovar(
    client, login_as, make_project, fill_project, profile
):
    project = fill_project(make_project())
    workflow.submit(project, by=project.leader)
    login_as(profile)
    assert client.post(reverse("projects:approve", args=[project.pk])).status_code == 403
    project.refresh_from_db()
    assert project.status == ProjectStatus.SUBMITTED


@pytest.mark.req("002:FR-012")
def test_so_o_lider_submete(make_project, fill_project, manager):
    project = fill_project(make_project())
    with pytest.raises(ValidationError, match="Só o líder"):
        workflow.submit(project, by=manager)


@pytest.mark.req("002:FR-016")
def test_detalhe_mostra_historico(client, open_project):
    project = open_project()
    client.force_login(project.leader)
    page = client.get(reverse("projects:detail", args=[project.pk])).content.decode()
    assert "Histórico de decisões" in page and "Aprovado" in page and project.code in page
