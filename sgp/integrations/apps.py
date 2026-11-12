from django.apps import AppConfig


class IntegrationsConfig(AppConfig):
    name = "sgp.integrations"
    label = "integrations"
    verbose_name = "Integração com o Sankhya"

    def ready(self):
        from sgp.audit.event_types import register_many

        from . import signals  # noqa: F401

        register_many(
            {
                "integration.sent": "Registro enviado ao Sankhya",
                "integration.failed": "Falha no envio ao Sankhya (alerta)",
                "integration.reprocessed": "Mensagem de integração reprocessada pela TI",
                "integration.exported": "Registros da integração exportados em arquivo",
                "integration.mapping_published": "Mapeamento do Sankhya publicado",
            }
        )
