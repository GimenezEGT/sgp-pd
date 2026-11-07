from django.apps import AppConfig


class SubdocumentsConfig(AppConfig):
    name = "sgp.subdocuments"
    label = "subdocuments"
    verbose_name = "Subdocumentos"

    def ready(self):
        from sgp.files import access

        from . import event_types  # noqa: F401
        from .permissions import subdocument_file_policy

        access.register(subdocument_file_policy)
