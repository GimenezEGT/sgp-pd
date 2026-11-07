"""TAP, equipe e marcos (história 2 da feature 002)."""

from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from sgp.accounts.profiles import Profile
from sgp.audit.models import AuditEvent
from sgp.projects import services, workflow
from sgp.vocab.models import SUBDOCUMENT_TYPE, get_term

pytestmark = pytest.mark.django_db


@pytest.mark.req("002:FR-004")
@pytest.mark.req("002:FR-019")
def test_tap_salvo_pela_tela_gera_evento_com_diff(client, make_project):
    project = make_project()
    client.force_login(project.leader)
    data = {
        "justification": "Demanda",
        "objective": "Lançar",
        "scope_included": "Formulação\nValidação",
        "deliverables": "Kit",
        "row_version": 0,
        "riscos-TOTAL_FORMS": 3,
        "riscos-INITIAL_FORMS": 0,
        "riscos-0-risco": "Atraso",
        "riscos-0-impacto": "Prazo",
        "riscos-0-resposta": "Plano B",
        "partes-TOTAL_FORMS": 3,
        "partes-INITIAL_FORMS": 0,
        "partes-0-nome_area": "Comercial",
        "partes-0-interesse": "Lançamento",
    }
    response = client.post(reverse("projects:charter", args=[project.pk]), data)
    assert response.status_code == 302
    charter = project.charter
    charter.refresh_from_db()
    assert charter.scope_included == ["Formulação", "Validação"]
    assert charter.risks == [{"risco": "Atraso", "impacto": "Prazo", "resposta": "Plano B"}]
    event = AuditEvent.objects.get(event_type="projects.charter_updated")
    assert event.old_value["scope_included"] == [] and event.new_value["scope_included"] == [
        "Formulação",
        "Validação",
    ]
    assert "constraints" not in event.new_value


@pytest.mark.req("002:FR-005")
def test_equipe_com_vigencia_e_encerramento_com_motivo(make_project, make_user):
    project = make_project()
    analyst = make_user("ana", Profile.ANALYST)
    member = services.add_member(project, by=project.leader, user=analyst, role="Formulação")
    with pytest.raises(ValidationError, match="já faz parte"):
        services.add_member(project, by=project.leader, user=analyst, role="Outro papel")
    with pytest.raises(ValidationError):
        services.end_member(member, by=project.leader, reason="")
    services.end_member(member, by=project.leader, reason="Mudou de área")
    member.refresh_from_db()
    assert member.end_date == timezone.localdate() and member.end_reason == "Mudou de área"
    assert project.members.filter(pk=member.pk).exists()
    assert AuditEvent.objects.filter(
        event_type="projects.member_ended", project_id=project.pk
    ).exists()


def test_vigencia_do_lider_nao_e_encerrada(make_project):
    project = make_project()
    leader_member = project.members.get(user=project.leader)
    with pytest.raises(ValidationError, match="líder"):
        services.end_member(leader_member, by=project.leader, reason="x")


@pytest.mark.req("002:FR-006")
def test_marcos_planejados_e_cancelados_sem_exclusao(make_project):
    project = make_project()
    entrada = get_term(SUBDOCUMENT_TYPE, "entrada")
    milestone = services.add_milestone(
        project, by=project.leader, subdocument_type=entrada, planned_date=date(2026, 12, 1)
    )
    assert milestone.actual_date is None
    services.update_milestone(milestone, by=project.leader, planned_date=date(2026, 12, 20))
    milestone.refresh_from_db()
    assert milestone.planned_date == date(2026, 12, 20)
    services.cancel_milestone(milestone, by=project.leader, reason="Replanejado")
    milestone.refresh_from_db()
    assert milestone.canceled_at is not None and project.milestones.count() == 1
    assert not project.milestones.active().exists()


@pytest.mark.req("002:FR-006")
@pytest.mark.req("002:FR-017")
def test_data_realizada_so_depois_de_aberto_e_validada(open_project):
    project = open_project()
    milestone = project.milestones.active().get()
    with pytest.raises(ValidationError, match="futuro"):
        services.update_milestone(
            milestone, by=project.leader, actual_date=timezone.localdate() + timedelta(days=1)
        )
    with pytest.raises(ValidationError, match="anterior à criação"):
        services.update_milestone(milestone, by=project.leader, actual_date=date(2020, 1, 1))
    services.update_milestone(milestone, by=project.leader, actual_date=timezone.localdate())
    milestone.refresh_from_db()
    assert milestone.actual_date == timezone.localdate()
    event = AuditEvent.objects.get(event_type="projects.milestone_updated")
    assert event.old_value == {"data_realizada": None}


def test_data_realizada_recusada_em_rascunho(make_project):
    project = make_project()
    milestone = services.add_milestone(
        project,
        by=project.leader,
        subdocument_type=get_term(SUBDOCUMENT_TYPE, "entrada"),
        planned_date=date(2026, 12, 1),
    )
    with pytest.raises(ValidationError, match="depois que o projeto é aberto"):
        services.update_milestone(milestone, by=project.leader, actual_date=timezone.localdate())


@pytest.mark.req("002:FR-013")
def test_submetido_fica_bloqueado(make_project, fill_project):
    project = fill_project(make_project())
    workflow.submit(project, by=project.leader)
    with pytest.raises(ValidationError, match="não pode ser editado"):
        services.update_charter(project, by=project.leader, data={"objective": "outro"})
    with pytest.raises(ValidationError, match="submetido"):
        services.add_member(project, by=project.leader, user=project.leader, role="x")


@pytest.mark.req("002:FR-017")
def test_aberto_bloqueia_tap_e_plano_mas_permite_equipe(open_project, make_user):
    project = open_project()
    with pytest.raises(ValidationError):
        services.update_charter(project, by=project.leader, data={"objective": "outro"})
    with pytest.raises(ValidationError):
        services.update_business_plan(
            project, by=project.leader, data={"objective": "outro"}, forecasts={}
        )
    services.add_member(
        project, by=project.leader, user=make_user(None, Profile.ANALYST), role="Validação"
    )


@pytest.mark.req("002:FR-020")
def test_tap_gravado_por_outra_pessoa_antes_e_recusado(make_project):
    project = make_project()
    services.update_charter(project, by=project.leader, data={"objective": "A"}, row_version=0)
    with pytest.raises(ValidationError, match="Outra pessoa gravou"):
        services.update_charter(project, by=project.leader, data={"objective": "B"}, row_version=0)


def test_so_o_lider_edita_o_tap(client, make_project, make_user):
    project = make_project()
    manager = make_user(None, Profile.RD_MANAGER)
    client.force_login(manager)
    assert client.get(reverse("projects:charter", args=[project.pk])).status_code == 403
    with pytest.raises(ValidationError, match="Só o líder"):
        services.update_charter(project, by=manager, data={"objective": "x"})
