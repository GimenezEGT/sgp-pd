from django.apps import AppConfig
from django.db import DEFAULT_DB_ALIAS
from django.db.models.signals import post_migrate


def record_reconstruction_events(sender=None, using=DEFAULT_DB_ALIAS, **kwargs) -> int:
    """Depois das migrações: evento na trilha para as versões reconstruídas (feature 016).

    Só age com o banco na última migração (os modelos atuais valem) e quando há versão
    reconstruída; sem isso, não faz nada.
    """
    from django.db import connections
    from django.db.migrations.executor import MigrationExecutor

    if using != DEFAULT_DB_ALIAS:
        return 0
    connection = connections[using]
    tables = set(connection.introspection.table_names())
    if not {"fulldoc_finaldocumentversion", "audit_auditevent"} <= tables:
        return 0
    from .history import REASON, record_missing_events
    from .models import FinalDocumentVersion

    if not FinalDocumentVersion.objects.filter(reason=REASON).exists():
        return 0
    executor = MigrationExecutor(connection)
    if executor.migration_plan(executor.loader.graph.leaf_nodes()):
        return 0
    return record_missing_events()


class FulldocConfig(AppConfig):
    name = "sgp.fulldoc"
    label = "fulldoc"
    verbose_name = "Documento completo do projeto"

    def ready(self):
        from sgp.documents import services as document_services

        from . import event_types  # noqa: F401
        from .services import lookup_code

        if lookup_code not in document_services.EXTRA_LOOKUPS:
            document_services.EXTRA_LOOKUPS.append(lookup_code)
        post_migrate.connect(
            record_reconstruction_events,
            sender=self,
            dispatch_uid="fulldoc_reconstruction_events",
        )
