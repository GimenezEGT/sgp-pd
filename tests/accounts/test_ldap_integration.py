"""Integração com servidor LDAP (marcador ldap: contêiner fictício de desenvolvimento)."""

import os
import socket
from urllib.parse import urlparse

import pytest
from django.test import override_settings
from django.urls import reverse

from sgp.accounts.ldap_config import build_ldap_settings
from sgp.accounts.models import LoginAttempt, ProfileAssignment, User
from sgp.accounts.profiles import Profile
from sgp.accounts.services import GENERIC_LOGIN_ERROR, UNAVAILABLE_ERROR

pytestmark = pytest.mark.django_db
BACKEND = ["sgp.accounts.ldap.SGPLDAPBackend"]
DEV_PASSWORD = "Senha#Dev01"


def ldap_reachable() -> bool:
    uri = os.environ.get("LDAP_SERVER_URI", "")
    if not uri:
        return False
    parsed = urlparse(uri)
    try:
        with socket.create_connection((parsed.hostname, parsed.port or 389), timeout=2):
            return True
    except OSError:
        return False


requires_ldap = pytest.mark.skipif(
    not ldap_reachable(), reason="LDAP de desenvolvimento indisponível"
)


def ldap_settings(**overrides):
    env = dict(os.environ)
    env.update(overrides)
    settings = build_ldap_settings(env)
    return override_settings(AUTHENTICATION_BACKENDS=BACKEND, DEBUG=True, **settings)


def post_login(client, username, password):
    return client.post(reverse("accounts:login"), {"username": username, "password": password})


@pytest.mark.ldap
@requires_ldap
@pytest.mark.req("001:FR-001")
@pytest.mark.req("001:FR-002")
def test_bind_real_cria_cadastro_com_atributos_da_rede(client):
    with ldap_settings(LDAP_PROFILE_GROUPS=""):
        response = post_login(client, "ana.analista", DEV_PASSWORD)
    assert response.status_code == 302
    user = User.objects.get(username="ana.analista")
    assert user.full_name == "Ana Analista (fictícia)"
    assert user.job_title == "Analista de P&D"
    assert user.email == "ana.analista@sgp.dev.local"
    assert not user.has_usable_password()


@pytest.mark.ldap
@requires_ldap
@pytest.mark.req("001:FR-004")
@pytest.mark.parametrize(
    "username,password",
    [("ana.analista", "errada"), ("ex.colaborador", DEV_PASSWORD), ("nao.existe", DEV_PASSWORD)],
)
def test_bind_real_recusa_senha_errada_conta_desativada_e_inexistente(client, username, password):
    with ldap_settings(LDAP_PROFILE_GROUPS=""):
        response = post_login(client, username, password)
    assert GENERIC_LOGIN_ERROR in response.content.decode()
    assert LoginAttempt.objects.get().result == LoginAttempt.Result.FAILURE


@pytest.mark.ldap
@requires_ldap
@pytest.mark.req("001:FR-013")
def test_grupo_real_concede_perfil(client):
    if not os.environ.get("LDAP_GROUP_SEARCH_BASE"):
        pytest.skip("Busca de grupos não configurada")
    mapping = '{"ANALYST": "cn=sgp-analistas,ou=groups,dc=sgp,dc=dev,dc=local"}'
    with ldap_settings(LDAP_PROFILE_GROUPS=mapping):
        response = post_login(client, "ana.analista", DEV_PASSWORD)
    assert response["Location"] == reverse("core:home")
    assignment = ProfileAssignment.objects.get(user__username="ana.analista")
    assert assignment.profile == Profile.ANALYST
    assert assignment.source == ProfileAssignment.Source.NETWORK_GROUP


@pytest.mark.req("001:FR-004")
def test_servidor_inacessivel_e_tratado_como_indisponivel(client):
    env = {
        "LDAP_SERVER_URI": "ldap://127.0.0.1:1",
        "LDAP_USER_SEARCH_BASE": "ou=people,dc=exemplo,dc=local",
        "LDAP_USER_FILTER": "(uid=%(user)s)",
        "LDAP_TIMEOUT_SECONDS": "2",
    }
    with override_settings(AUTHENTICATION_BACKENDS=BACKEND, **build_ldap_settings(env)):
        response = post_login(client, "qualquer", "senha")
    assert UNAVAILABLE_ERROR in response.content.decode()
    assert LoginAttempt.objects.get().result == LoginAttempt.Result.UNAVAILABLE
