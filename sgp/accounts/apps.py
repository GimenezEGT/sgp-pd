from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "sgp.accounts"
    label = "accounts"
    verbose_name = "Pessoas e perfis"

    def ready(self):
        from . import checks, event_types, ldap  # noqa: F401

        ldap.connect_signals()
