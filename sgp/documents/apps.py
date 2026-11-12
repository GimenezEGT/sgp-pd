from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    name = "sgp.documents"
    label = "documents"
    verbose_name = "Geração de documentos"

    def ready(self):
        from . import event_types  # noqa: F401
