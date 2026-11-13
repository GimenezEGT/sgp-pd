"""Eventos do documento completo do projeto (contrato rotas-ui.md da feature 009)."""

from sgp.audit.event_types import register_many

register_many(
    {
        "fulldoc.requested": "Documento completo do projeto pedido",
        "fulldoc.generated": "Documento completo do projeto gerado e arquivado",
        "fulldoc.reused": "Documento completo do projeto reaproveitado (nada mudou)",
        "fulldoc.failed": "Falha na geração do documento completo do projeto (alerta)",
        "fulldoc.downloaded": "Documento completo do projeto baixado",
        "fulldoc.version_created": "Nova versão do documento final do projeto",
    }
)
