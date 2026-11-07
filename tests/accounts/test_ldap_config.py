"""Leitura da configuração LDAP a partir do ambiente (contrato configuracao.md)."""

import ldap
import pytest
from django.core.exceptions import ImproperlyConfigured
from django_auth_ldap.config import GroupOfNamesType, NestedActiveDirectoryGroupType

from sgp.accounts.ldap_config import build_ldap_settings, parse_profile_groups

BASE_ENV = {
    "LDAP_SERVER_URI": "ldaps://ad.empresa.local",
    "LDAP_USER_SEARCH_BASE": "OU=Pessoas,DC=empresa,DC=local",
}


def test_mapa_de_grupos_normalizado():
    raw = '{"ANALYST": "CN=SGP-Analistas,OU=Grupos,DC=empresa,DC=local"}'
    assert parse_profile_groups(raw) == {
        "ANALYST": "cn=sgp-analistas,ou=grupos,dc=empresa,dc=local"
    }
    assert parse_profile_groups("") == {}


@pytest.mark.parametrize("raw", ["não é json", "[1, 2]", '{"CHEFE": "cn=x"}', '{"ANALYST": ""}'])
def test_mapa_de_grupos_invalido(raw):
    with pytest.raises(ImproperlyConfigured):
        parse_profile_groups(raw)


def test_padroes_do_active_directory():
    settings = build_ldap_settings(
        {**BASE_ENV, "LDAP_GROUP_SEARCH_BASE": "OU=Grupos,DC=empresa,DC=local"}
    )
    assert settings["AUTH_LDAP_USER_SEARCH"].filterstr == "(sAMAccountName=%(user)s)"
    assert isinstance(settings["AUTH_LDAP_GROUP_TYPE"], NestedActiveDirectoryGroupType)
    assert settings["AUTH_LDAP_USER_ATTR_MAP"]["job_title"] == "title"
    assert settings["AUTH_LDAP_CONNECTION_OPTIONS"][ldap.OPT_REFERRALS] == 0
    assert settings["AUTH_LDAP_ALWAYS_UPDATE_USER"] is True


def test_grupo_de_desenvolvimento_e_ca_da_empresa():
    settings = build_ldap_settings(
        {
            **BASE_ENV,
            "LDAP_GROUP_SEARCH_BASE": "ou=groups,dc=sgp,dc=dev,dc=local",
            "LDAP_GROUP_TYPE": "group_of_names",
            "LDAP_CA_CERT_FILE": "/etc/ssl/certs/ca-empresa.pem",
            "LDAP_START_TLS": "true",
        }
    )
    assert isinstance(settings["AUTH_LDAP_GROUP_TYPE"], GroupOfNamesType)
    assert (
        settings["AUTH_LDAP_GLOBAL_OPTIONS"][ldap.OPT_X_TLS_CACERTFILE]
        == "/etc/ssl/certs/ca-empresa.pem"
    )
    assert settings["AUTH_LDAP_START_TLS"] is True


def test_tipo_de_grupo_desconhecido():
    with pytest.raises(ImproperlyConfigured):
        build_ldap_settings({**BASE_ENV, "LDAP_GROUP_SEARCH_BASE": "x", "LDAP_GROUP_TYPE": "outro"})
