from django.apps import AppConfig


class SignaturesConfig(AppConfig):
    name = "sgp.signatures"
    label = "signatures"
    verbose_name = "Assinatura eletrônica"

    def ready(self):
        from . import event_types  # noqa: F401
