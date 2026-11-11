"""Eventos da geração de documentos (contrato eventos-auditoria.md da feature 006)."""

from sgp.audit.event_types import register_many

register_many(
    {
        "documents.requested": "Geração de documento pedida",
        "documents.generated": "Documento gerado",
        "documents.generation_failed": "Falha na geração de documento (alerta)",
        "documents.regeneration_mismatch": "Regeneração com conteúdo diferente do arquivado (alerta)",
        "documents.frozen": "Conteúdo de geração congelado na aprovação",
        "documents.downloaded": "Documento gerado baixado",
        "documents.verification_lookup": "Código de verificação consultado",
        "layouts.draft_created": "Rascunho de modelo de layout criado",
        "layouts.draft_updated": "Rascunho de modelo de layout alterado",
        "layouts.published": "Modelo de layout publicado",
    }
)
