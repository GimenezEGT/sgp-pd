"""Eventos do ciclo de revisão e assinatura (contrato eventos-auditoria.md da feature 005)."""

from sgp.audit.event_types import register_many

register_many(
    {
        "signatures.submitted": "Documento enviado para revisão",
        "signatures.signed": "Documento assinado",
        "signatures.failed": "Falha de senha na assinatura",
        "signatures.blocked": "Assinatura bloqueada por falhas (alerta)",
        "signatures.returned": "Documento devolvido na revisão",
        "signatures.approved": "Documento aprovado com assinatura",
        "signatures.new_version": "Nova versão de documento",
        "signatures.verified": "Integridade do documento verificada",
        "signatures.delegation_created": "Delegação de aprovação criada",
        "signatures.delegation_ended": "Delegação de aprovação encerrada",
    }
)
