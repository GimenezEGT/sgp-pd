from django.apps import AppConfig


class StudiesConfig(AppConfig):
    name = "sgp.studies"
    label = "studies"
    verbose_name = "Estudos de desempenho e estabilidade"

    def ready(self):
        from . import event_types  # noqa: F401
