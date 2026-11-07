"""Perfis somados e recusa registrada (FR-009, FR-015)."""

import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import reverse

from sgp.accounts.models import ProfileAssignment
from sgp.accounts.profiles import (
    GLOBAL_PROJECT_ACCESS,
    Profile,
    active_profiles,
    clear_profile_cache,
    has_profile,
    profile_required,
)
from sgp.audit.models import AuditEvent

pytestmark = pytest.mark.django_db


@pytest.mark.req("001:FR-009")
def test_seis_perfis_do_plano():
    assert [label for _, label in Profile.choices] == [
        "Administrador do sistema",
        "Gestor de P&D",
        "Líder de projeto",
        "Analista/Pesquisador",
        "Qualidade/Assuntos Regulatórios",
        "Leitor",
    ]
    assert GLOBAL_PROJECT_ACCESS == {Profile.ADMIN, Profile.RD_MANAGER, Profile.QUALITY}


@pytest.mark.req("001:FR-009")
def test_permissoes_sao_a_soma_dos_perfis(client, login_as):
    login_as(Profile.READER, Profile.QUALITY)
    assert client.get(reverse("audit:trail")).status_code == 200
    assert client.get(reverse("audit:integrity")).status_code == 200
    assert client.get(reverse("accounts:people")).status_code == 403


def test_perfil_revogado_nao_conta(make_user):
    user = make_user("x", Profile.ANALYST, Profile.READER)
    ProfileAssignment.objects.filter(user=user, profile=Profile.READER).update(
        revoked_at="2026-01-01T00:00:00Z"
    )
    clear_profile_cache(user)
    assert active_profiles(user, refresh=True) == {Profile.ANALYST}
    assert has_profile(user, Profile.ANALYST) and not has_profile(user, Profile.READER)


@pytest.mark.req("001:FR-015")
def test_decorator_recusa_com_403_e_registra(make_user):
    user = make_user("leitor", Profile.READER)

    @profile_required(Profile.ADMIN)
    def view(request):
        return HttpResponse("ok")

    request = RequestFactory().get("/administracao/teste/")
    request.user = user
    response = view(request)
    assert response.status_code == 403
    event = AuditEvent.objects.get(event_type="auth.permission_denied")
    assert event.actor == user
    assert event.new_value == {
        "rota": "/administracao/teste/",
        "metodo": "GET",
        "motivo": "perfil exigido: Administrador do sistema",
    }
    assert view.sgp_required_profiles == {Profile.ADMIN}
