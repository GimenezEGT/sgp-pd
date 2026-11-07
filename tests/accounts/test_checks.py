"""Canal cifrado com o serviço de autenticação (FR-027)."""

import pytest
from django.test import override_settings

from sgp.accounts.checks import LDAP_BACKEND, check_ldap_encryption

pytestmark = pytest.mark.req("001:FR-027")


def run(**settings):
    defaults = {
        "DEBUG": False,
        "AUTHENTICATION_BACKENDS": [LDAP_BACKEND],
        "AUTH_LDAP_START_TLS": False,
    }
    defaults.update(settings)
    with override_settings(**defaults):
        return [error.id for error in check_ldap_encryption()]


def test_ldap_sem_criptografia_e_recusado_em_producao():
    assert run(AUTH_LDAP_SERVER_URI="ldap://ad.empresa.local") == ["sgp.E002"]


def test_ldaps_e_aceito():
    assert run(AUTH_LDAP_SERVER_URI="ldaps://ad.empresa.local") == []


def test_starttls_e_aceito():
    assert run(AUTH_LDAP_SERVER_URI="ldap://ad.empresa.local", AUTH_LDAP_START_TLS=True) == []


def test_uri_ausente_e_recusada():
    assert run(AUTH_LDAP_SERVER_URI="") == ["sgp.E001"]


def test_desenvolvimento_nao_exige_criptografia():
    assert run(DEBUG=True, AUTH_LDAP_SERVER_URI="ldap://ldap:389") == []
