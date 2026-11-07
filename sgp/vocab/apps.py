from django.apps import AppConfig


class VocabConfig(AppConfig):
    name = "sgp.vocab"
    label = "vocab"
    verbose_name = "Listas controladas"

    def ready(self):
        from . import event_types  # noqa: F401
