from django.apps import AppConfig


class NotebookConfig(AppConfig):
    name = "sgp.notebook"
    label = "notebook"
    verbose_name = "Caderno de laboratório eletrônico"

    def ready(self):
        from sgp.files import access

        from . import event_types  # noqa: F401
        from .permissions import notebook_file_policy

        access.register(notebook_file_policy)
