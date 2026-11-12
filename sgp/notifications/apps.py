from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    name = "sgp.notifications"
    label = "notifications"
    verbose_name = "Notificações por e-mail"

    def ready(self):
        from . import event_types, signals  # noqa: F401
