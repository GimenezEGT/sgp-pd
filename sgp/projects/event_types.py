"""Eventos de projeto (contrato eventos-auditoria.md da feature 002) e mascaramento financeiro."""

from sgp.audit import masking
from sgp.audit.event_types import register_many

from .permissions import FINANCIAL_FIELDS, financial_viewer_rule

register_many(
    {
        "projects.created": "Projeto criado",
        "projects.updated": "Dados do produto alterados",
        "projects.charter_updated": "TAP alterado",
        "projects.business_plan_updated": "Plano de Negócios alterado",
        "projects.member_added": "Membro incluído na equipe",
        "projects.member_ended": "Vigência de membro encerrada",
        "projects.milestone_added": "Marco incluído",
        "projects.milestone_updated": "Marco alterado",
        "projects.milestone_canceled": "Marco cancelado",
        "projects.submitted": "Projeto submetido",
        "projects.returned": "Projeto devolvido",
        "projects.approved": "Projeto aprovado e aberto",
        "projects.version_changed": "Versão do projeto alterada",
    }
)

masking.register("projects.business_plan_updated", FINANCIAL_FIELDS, financial_viewer_rule)
