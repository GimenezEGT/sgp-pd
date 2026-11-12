"""Eventos da revisão controlada de modelos (contrato eventos-auditoria.md da feature 013)."""

from sgp.audit.event_types import register_many

register_many(
    {
        "templates.submitted": "Revisão de modelo enviada para aprovação",
        "templates.returned": "Revisão de modelo devolvida",
        "templates.approved": "Revisão de modelo aprovada com assinatura",
        "templates.became_current": "Versão de modelo entrou em vigência",
        "templates.discarded": "Revisão de modelo descartada",
        "templates.verified": "Integridade de versão de modelo verificada",
        "templates.retirement_requested": "Retirada de modelo pedida",
        "templates.retirement_approved": "Retirada de modelo aprovada com assinatura",
        "templates.retirement_returned": "Retirada de modelo devolvida",
    }
)
