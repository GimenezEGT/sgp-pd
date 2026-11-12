from django.apps import AppConfig


class DashboardConfig(AppConfig):
    name = "sgp.dashboard"
    label = "dashboard"
    verbose_name = "Painel do gestor"

    def ready(self):
        from sgp.audit.event_types import register_many

        register_many({"dashboard.exported": "Carteira de projetos exportada em planilha"})
