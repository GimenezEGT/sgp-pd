"""Eventos dos cadastros (contrato eventos-auditoria.md da feature 003)."""

from sgp.audit.event_types import register_many

register_many(
    {
        "catalog.created": "Cadastro criado",
        "catalog.updated": "Cadastro corrigido",
        "catalog.versioned": "Nova versão de cadastro",
        "catalog.locked": "Cadastro bloqueado por documento assinado",
        "catalog.deactivated": "Cadastro desativado",
        "catalog.reactivated": "Cadastro reativado",
        "catalog.import_previewed": "Importação de insumos pré-visualizada",
        "catalog.import_confirmed": "Importação de insumos confirmada",
        "catalog.import_rejections_exported": "Relatório de rejeições exportado",
    }
)
