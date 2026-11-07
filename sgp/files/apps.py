from django.apps import AppConfig


class FilesConfig(AppConfig):
    name = "sgp.files"
    label = "files"
    verbose_name = "Arquivos"

    def ready(self):
        from . import event_types  # noqa: F401
