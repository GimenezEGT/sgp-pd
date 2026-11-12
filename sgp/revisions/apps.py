from django.apps import AppConfig


class RevisionsConfig(AppConfig):
    name = "sgp.revisions"
    label = "revisions"
    verbose_name = "Revisão controlada de modelos"

    def ready(self):
        from . import event_types  # noqa: F401
