from django.apps import AppConfig


class AuditConfig(AppConfig):
    name = "sgp.audit"
    label = "audit"
    verbose_name = "Trilha de auditoria"

    def ready(self):
        from . import event_types  # noqa: F401
