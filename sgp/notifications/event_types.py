"""Eventos das notificações (contrato notificacoes.md da feature 010)."""

from sgp.audit.event_types import register_many

register_many(
    {
        "notifications.sent": "Notificação por e-mail enviada",
        "notifications.failed": "Falha no envio de notificação por e-mail (alerta)",
        "notifications.skipped": "Notificação por e-mail omitida (preferência ou sem e-mail)",
        "notifications.preference_changed": "Preferências de notificação alteradas",
    }
)
