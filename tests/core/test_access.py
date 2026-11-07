"""Regra única de acesso a projetos (FR-014)."""

import pytest
from django.contrib.auth.models import AnonymousUser

from sgp.accounts.models import ProfileAssignment
from sgp.accounts.profiles import Profile
from sgp.core.access import can_access_project

pytestmark = [pytest.mark.django_db, pytest.mark.req("001:FR-014")]


class StubProject:
    def __init__(self, *members):
        self.members = {member.pk for member in members}

    def is_member(self, user):
        return user.pk in self.members


@pytest.mark.parametrize("profile", [Profile.ADMIN, Profile.RD_MANAGER, Profile.QUALITY])
def test_perfis_globais_acessam_todos_os_projetos(make_user, profile):
    user = make_user(None, profile)
    assert can_access_project(user, StubProject())


@pytest.mark.parametrize("profile", [Profile.PROJECT_LEADER, Profile.ANALYST, Profile.READER])
def test_demais_perfis_so_acessam_projetos_de_que_sao_membros(make_user, profile):
    user = make_user(None, profile)
    assert not can_access_project(user, StubProject())
    assert can_access_project(user, StubProject(user))


def test_sem_perfil_ou_anonimo_nao_acessa(make_user):
    user = make_user("sem.perfil")
    assert not can_access_project(user, StubProject(user))
    assert not can_access_project(AnonymousUser(), StubProject())
    assert not can_access_project(None, StubProject())


def test_pessoa_desativada_nao_acessa(make_user):
    user = make_user("desativada", Profile.ADMIN)
    user.is_active = False
    user.save()
    assert not can_access_project(user, StubProject(user))


def test_perfil_revogado_deixa_de_valer(make_user):
    user = make_user("revogada", Profile.QUALITY)
    ProfileAssignment.objects.filter(user=user).update(revoked_at="2026-01-01T00:00:00Z")
    assert not can_access_project(user, StubProject())
