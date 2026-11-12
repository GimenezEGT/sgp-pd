from django.apps import AppConfig


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
