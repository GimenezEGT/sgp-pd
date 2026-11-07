"""Sincronização de perfis com grupos da rede (FR-013)."""

import pytest
from django.test import override_settings
from django.urls import reverse

from sgp.accounts.models import ProfileAssignment
from sgp.accounts.profiles import Profile
from sgp.audit.models import AuditEvent

pytestmark = [pytest.mark.django_db, pytest.mark.req("001:FR-013")]

ANALYSTS = "cn=sgp-analistas,ou=groups,dc=empresa,dc=local"
ADMINS = "cn=sgp-administradores,ou=groups,dc=empresa,dc=local"
MAPPING = {Profile.ANALYST: ANALYSTS, Profile.ADMIN: ADMINS}


def login(client, username):
    client.logout()
    return client.post(
        reverse("accounts:login"), {"username": username, "password": "Senha#Teste1"}
    )


@override_settings(LDAP_PROFILE_GROUPS=MAPPING)
def test_grupo_concede_perfil_no_login(client, directory):
    directory.add_person("ana", groups=[ANALYSTS.upper()])
    response = login(client, "ana")
    assert response["Location"] == reverse("core:home")
    assignment = ProfileAssignment.objects.get(user__username="ana")
    assert assignment.profile == Profile.ANALYST
    assert assignment.source == ProfileAssignment.Source.NETWORK_GROUP
    assert assignment.source_group == ANALYSTS
    event = AuditEvent.objects.get(event_type="accounts.profile_granted")
    assert event.actor is None and ANALYSTS in event.reason


@override_settings(LDAP_PROFILE_GROUPS=MAPPING)
def test_saida_do_grupo_revoga_so_perfil_sincronizado(client, directory, make_user):
    admin = make_user("admin", Profile.ADMIN)
    directory.add_person("ana", groups=[ANALYSTS])
    login(client, "ana")
    ana = ProfileAssignment.objects.get(user__username="ana").user
    ProfileAssignment.objects.create(
        user=ana,
        profile=Profile.READER,
        granted_by=admin,
        grant_reason="manual",
        approval_reference="ok",
    )
    directory.set_groups("ana", [])
    login(client, "ana")
    analyst = ProfileAssignment.objects.get(user=ana, profile=Profile.ANALYST)
    reader = ProfileAssignment.objects.get(user=ana, profile=Profile.READER)
    assert analyst.revoked_at is not None and ANALYSTS in analyst.revoke_reason
    assert reader.revoked_at is None


@override_settings(LDAP_PROFILE_GROUPS=MAPPING)
def test_concessao_manual_nao_e_revogada_pela_sincronizacao(client, directory, make_user):
    make_user("ana", Profile.ANALYST)
    directory.add_person("ana", groups=[])
    login(client, "ana")
    assert ProfileAssignment.objects.get(user__username="ana").revoked_at is None


@override_settings(LDAP_PROFILE_GROUPS=MAPPING)
def test_ultimo_administrador_sincronizado_e_mantido(client, directory):
    directory.add_person("chefe", groups=[ADMINS])
    login(client, "chefe")
    directory.set_groups("chefe", [])
    login(client, "chefe")
    assert ProfileAssignment.objects.get(user__username="chefe").revoked_at is None


def test_sem_mapeamento_nada_e_sincronizado(client, directory):
    directory.add_person("ana", groups=[ANALYSTS])
    response = login(client, "ana")
    assert response["Location"] == reverse("accounts:access_request")
    assert not ProfileAssignment.objects.exists()
