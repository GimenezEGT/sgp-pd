"""Eventos de arquivos (contrato eventos-auditoria.md da feature 003)."""

from sgp.audit.event_types import register_many

register_many(
    {
        "files.uploaded": "Arquivo anexado",
        "files.integrity_failed": "Arquivo com resumo divergente",
    }
)
