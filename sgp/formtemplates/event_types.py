"""Eventos dos modelos de formulário (contrato eventos-auditoria.md da feature 004)."""

from sgp.audit.event_types import register_many

register_many(
    {
        "formtemplates.draft_created": "Rascunho de modelo criado",
        "formtemplates.draft_updated": "Rascunho de modelo alterado",
        "formtemplates.published": "Modelo publicado",
    }
)
