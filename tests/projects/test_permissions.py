"""Acesso ao projeto e permissão financeira (FR-003, FR-010 da feature 002)."""

import pytest
from django.test import override_settings

from sgp.accounts.profiles import Profile
from sgp.core.access import can_access_project
from sgp.projects.permissions import can_decide, can_edit_documents, can_view_financials

pytestmark = pytest.mark.django_db


@pytest.mark.req("002:FR-003")
def test_rascunho_so_para_lider_e_perfis_globais(make_project, make_user):
    project = make_project()
    analyst = make_user(None, Profile.ANALYST)
    project.members.create(user=analyst, role="Analista", added_by=project.leader)
    assert can_access_project(project.leader, project)
    assert not can_access_project(analyst, project)
    for profile in (Profile.RD_MANAGER, Profile.QUALITY, Profile.ADMIN):
        assert can_access_project(make_user(None, profile), project)


@pytest.mark.req("002:FR-015")
def test_equipe_acessa_depois_da_aprovacao(open_project, make_user):
    project = open_project()
    analyst = make_user(None, Profile.ANALYST)
    assert not can_access_project(analyst, project)
    project.members.create(user=analyst, role="Analista", added_by=project.leader)
    assert can_access_project(analyst, project)


@pytest.mark.req("002:FR-010")
def test_quem_ve_dados_financeiros(make_project, make_user):
    project = make_project()
    assert can_view_financials(project.leader, project)
    assert can_view_financials(make_user(None, Profile.RD_MANAGER), project)
    for profile in (
        Profile.QUALITY,
        Profile.ADMIN,
        Profile.ANALYST,
        Profile.READER,
        Profile.PROJECT_LEADER,
    ):
        assert not can_view_financials(make_user(None, profile), project), profile


@pytest.mark.req("002:FR-010")
@override_settings(FINANCIAL_DATA_PROFILES=["QUALITY"])
def test_perfis_autorizados_por_configuracao(make_project, make_user):
    assert can_view_financials(make_user(None, Profile.QUALITY), make_project())


@pytest.mark.req("002:FR-014")
def test_lider_que_tambem_e_gestor_nao_decide(make_user, make_project):
    leader = make_user("lider.gestor", Profile.PROJECT_LEADER, Profile.RD_MANAGER)
    project = make_project(leader=leader)
    assert not can_decide(leader, project)
    assert can_decide(make_user(None, Profile.RD_MANAGER), project)


def test_so_o_lider_edita_documentos(make_project, make_user):
    project = make_project()
    assert can_edit_documents(project.leader, project)
    assert not can_edit_documents(make_user(None, Profile.RD_MANAGER), project)
