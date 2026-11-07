"""Montagem das settings do django-auth-ldap a partir de variáveis de ambiente.

Usado por config/settings.py; não importa modelos do Django.
"""

import json
from collections.abc import Mapping

from django.core.exceptions import ImproperlyConfigured

PROFILE_CODES = {"ADMIN", "RD_MANAGER", "PROJECT_LEADER", "ANALYST", "QUALITY", "READER"}


def _bool(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "sim", "on"}


def parse_profile_groups(raw: str | None) -> dict[str, str]:
    """Converte LDAP_PROFILE_GROUPS (JSON perfil → DN do grupo) em dicionário normalizado."""
    if not raw or not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ImproperlyConfigured(
            "LDAP_PROFILE_GROUPS deve ser um JSON perfil → DN do grupo."
        ) from exc
    if not isinstance(data, dict):
        raise ImproperlyConfigured("LDAP_PROFILE_GROUPS deve ser um objeto JSON.")
    result = {}
    for profile, dn in data.items():
        if profile not in PROFILE_CODES:
            raise ImproperlyConfigured(f"Perfil desconhecido em LDAP_PROFILE_GROUPS: {profile}.")
        if not isinstance(dn, str) or not dn.strip():
            raise ImproperlyConfigured(f"DN de grupo vazio para o perfil {profile}.")
        result[profile] = dn.strip().lower()
    return result


def build_ldap_settings(env: Mapping[str, str]) -> dict:
    import ldap
    from django_auth_ldap.config import (
        ActiveDirectoryGroupType,
        GroupOfNamesType,
        LDAPSearch,
        NestedActiveDirectoryGroupType,
    )

    timeout = int(env.get("LDAP_TIMEOUT_SECONDS", "") or 5)
    settings = {
        "AUTH_LDAP_SERVER_URI": env.get("LDAP_SERVER_URI", ""),
        "AUTH_LDAP_BIND_DN": env.get("LDAP_BIND_DN", ""),
        "AUTH_LDAP_BIND_PASSWORD": env.get("LDAP_BIND_PASSWORD", ""),
        "AUTH_LDAP_START_TLS": _bool(env.get("LDAP_START_TLS")),
        "AUTH_LDAP_ALWAYS_UPDATE_USER": True,
        "AUTH_LDAP_CACHE_TIMEOUT": 0,
        "AUTH_LDAP_MIRROR_GROUPS": False,
        "AUTH_LDAP_FIND_GROUP_PERMS": False,
        "AUTH_LDAP_USER_ATTR_MAP": {
            "first_name": env.get("LDAP_ATTR_FIRST_NAME", "") or "givenName",
            "last_name": env.get("LDAP_ATTR_LAST_NAME", "") or "sn",
            "full_name": env.get("LDAP_ATTR_FULL_NAME", "") or "displayName",
            "email": env.get("LDAP_ATTR_EMAIL", "") or "mail",
            "job_title": env.get("LDAP_ATTR_JOB_TITLE", "") or "title",
        },
        "AUTH_LDAP_CONNECTION_OPTIONS": {
            ldap.OPT_REFERRALS: 0,
            ldap.OPT_NETWORK_TIMEOUT: timeout,
            ldap.OPT_TIMEOUT: timeout,
        },
        "AUTH_LDAP_GLOBAL_OPTIONS": {},
        "LDAP_PROFILE_GROUPS": parse_profile_groups(env.get("LDAP_PROFILE_GROUPS")),
    }

    user_base = env.get("LDAP_USER_SEARCH_BASE", "")
    if user_base:
        settings["AUTH_LDAP_USER_SEARCH"] = LDAPSearch(
            user_base,
            ldap.SCOPE_SUBTREE,
            env.get("LDAP_USER_FILTER", "") or "(sAMAccountName=%(user)s)",
        )

    ca_file = env.get("LDAP_CA_CERT_FILE", "")
    if ca_file:
        settings["AUTH_LDAP_GLOBAL_OPTIONS"] = {
            ldap.OPT_X_TLS_CACERTFILE: ca_file,
            ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_DEMAND,
        }

    group_base = env.get("LDAP_GROUP_SEARCH_BASE", "")
    if group_base:
        group_types = {
            "active_directory_nested": NestedActiveDirectoryGroupType,
            "active_directory": ActiveDirectoryGroupType,
            "group_of_names": GroupOfNamesType,
        }
        type_name = env.get("LDAP_GROUP_TYPE", "") or "active_directory_nested"
        if type_name not in group_types:
            raise ImproperlyConfigured(f"LDAP_GROUP_TYPE desconhecido: {type_name}.")
        settings["AUTH_LDAP_GROUP_SEARCH"] = LDAPSearch(
            group_base,
            ldap.SCOPE_SUBTREE,
            env.get("LDAP_GROUP_FILTER", "") or "(objectClass=group)",
        )
        settings["AUTH_LDAP_GROUP_TYPE"] = group_types[type_name]()
    return settings
