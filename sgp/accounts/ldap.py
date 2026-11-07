"""Integração com o Active Directory: backend, indisponibilidade e grupos da rede."""

import contextvars
import logging

from django_auth_ldap.backend import LDAPBackend, ldap_error

logger = logging.getLogger(__name__)

_unavailable: contextvars.ContextVar = contextvars.ContextVar("sgp_ldap_unavailable", default=False)


def reset_unavailable() -> None:
    _unavailable.set(False)


def was_unavailable() -> bool:
    return _unavailable.get()


def _unavailable_exceptions() -> tuple:
    import ldap

    names = ("SERVER_DOWN", "TIMEOUT", "CONNECT_ERROR", "TIMELIMIT_EXCEEDED")
    return tuple(getattr(ldap, name) for name in names if hasattr(ldap, name))


def _on_ldap_error(sender, context=None, exception=None, **kwargs):
    if isinstance(exception, _unavailable_exceptions()):
        _unavailable.set(True)
        logger.warning("Serviço de autenticação indisponível (%s).", type(exception).__name__)


def connect_signals() -> None:
    ldap_error.connect(_on_ldap_error, dispatch_uid="sgp_ldap_unavailable")


class SGPLDAPBackend(LDAPBackend):
    """Backend LDAP com login normalizado em minúsculas."""

    def ldap_to_django_username(self, username):
        return username.strip().lower()


def network_group_dns(user) -> set[str]:
    """DNs (minúsculos) dos grupos da rede da pessoa autenticada; vazio sem busca de grupos."""
    ldap_user = getattr(user, "ldap_user", None)
    if ldap_user is not None:
        from django.conf import settings

        if getattr(settings, "AUTH_LDAP_GROUP_SEARCH", None) is None:
            return set()
        try:
            return {dn.lower() for dn in ldap_user.group_dns}
        except Exception:  # noqa: BLE001 - falha de grupos não impede o login
            logger.exception("Não foi possível ler os grupos da rede de %s.", user.username)
            return set()
    return {dn.lower() for dn in getattr(user, "network_group_dns", set())}
