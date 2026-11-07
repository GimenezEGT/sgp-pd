"""Verificações de sistema da autenticação (FR-027: canal cifrado com o AD)."""

from django.conf import settings
from django.core.checks import Error, register

LDAP_BACKEND = "sgp.accounts.ldap.SGPLDAPBackend"


@register("security")
def check_ldap_encryption(app_configs=None, **kwargs):
    if settings.DEBUG or LDAP_BACKEND not in settings.AUTHENTICATION_BACKENDS:
        return []
    uri = (getattr(settings, "AUTH_LDAP_SERVER_URI", "") or "").strip()
    if not uri:
        return [Error("LDAP_SERVER_URI não está configurado.", id="sgp.E001")]
    if not uri.lower().startswith("ldaps://") and not getattr(
        settings, "AUTH_LDAP_START_TLS", False
    ):
        return [
            Error(
                "A conexão com o serviço de autenticação da rede precisa ser cifrada.",
                hint="Use LDAP_SERVER_URI=ldaps://... ou LDAP_START_TLS=true.",
                id="sgp.E002",
            )
        ]
    return []
