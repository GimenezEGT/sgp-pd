"""Toda edição de projeto, TAP, plano, equipe e marcos gera evento com valores (FR-019, SC-004)."""

from datetime import date
from decimal import Decimal

import pytest

from sgp.accounts.profiles import Profile
from sgp.audit.models import AuditEvent
from sgp.projects import services
from sgp.vocab.models import SUBDOCUMENT_TYPE, get_term

pytestmark = [pytest.mark.django_db, pytest.mark.req("002:FR-019"), pytest.mark.req("002:SC-004")]


def test_cada_tipo_de_edicao_gera_evento_do_projeto(make_project, make_user):
    project = make_project()
    leader = project.leader
    services.update_product(project, by=leader, data={"product_family": "Família X"})
    services.update_charter(project, by=leader, data={"objective": "Novo objetivo"})
    services.update_business_plan(
        project, by=leader, data={"objective": "Plano"}, forecasts={1: Decimal("1.00")}
    )
    member = services.add_member(
        project, by=leader, user=make_user(None, Profile.ANALYST), role="Formulação"
    )
    services.end_member(member, by=leader, reason="Saiu")
    milestone = services.add_milestone(
        project,
        by=leader,
        subdocument_type=get_term(SUBDOCUMENT_TYPE, "rapd"),
        planned_date=date(2027, 1, 10),
    )
    services.update_milestone(milestone, by=leader, planned_date=date(2027, 2, 10))
    services.cancel_milestone(milestone, by=leader, reason="Replanejado")

    events = {e.event_type: e for e in AuditEvent.objects.filter(project_id=project.pk)}
    expected = {
        "projects.created",
        "projects.updated",
        "projects.charter_updated",
        "projects.business_plan_updated",
        "projects.member_added",
        "projects.member_ended",
        "projects.milestone_added",
        "projects.milestone_updated",
        "projects.milestone_canceled",
    }
    assert expected <= set(events)
    assert events["projects.updated"].old_value == {"product_family": ""}
    assert events["projects.charter_updated"].new_value == {"objective": "Novo objetivo"}
    plan_event = events["projects.business_plan_updated"]
    assert (
        plan_event.old_value["forecasts"]["1"] is None
        and plan_event.new_value["forecasts"]["1"] == "1.00"
    )
    assert events["projects.milestone_updated"].old_value == {"data_planejada": "2027-01-10"}
    assert all(event.actor == leader for event in events.values())


def test_gravacao_sem_mudanca_nao_gera_evento(make_project):
    project = make_project()
    services.update_charter(project, by=project.leader, data={"objective": ""})
    assert not AuditEvent.objects.filter(event_type="projects.charter_updated").exists()
