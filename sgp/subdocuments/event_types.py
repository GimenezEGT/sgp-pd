"""Eventos dos subdocumentos (contrato eventos-auditoria.md da feature 004)."""

from sgp.audit.event_types import register_many

register_many(
    {
        "subdocuments.created": "Subdocumento criado",
        "subdocuments.updated": "Subdocumento alterado",
        "subdocuments.flow_authorized": "Criação fora da ordem autorizada",
        "subdocuments.derived_refreshed": "Linhas derivadas atualizadas",
        "subdocuments.template_migrated": "Subdocumento migrado de modelo",
        "subdocuments.approved": "Subdocumento aprovado (confirmação)",
        "subdocuments.review_requested": "Subdocumento marcado para revisão",
    }
)
