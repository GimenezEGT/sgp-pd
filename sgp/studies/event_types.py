"""Eventos dos estudos (contrato rotas-ui.md da feature 007)."""

from sgp.audit.event_types import register_many

register_many(
    {
        "studies.created": "Estudo criado",
        "studies.updated": "Medidas do estudo gravadas e recalculadas",
        "studies.criteria_set": "Critério de aceitação do estudo definido",
        "studies.not_applicable": "Estudo marcado como não aplicável",
        "studies.imported": "Medidas importadas para o estudo",
        "studies.mapping_saved": "Mapeamento de importação salvo",
        "studies.locked": "Estudo bloqueado pela aprovação do documento",
        "studies.new_version": "Nova versão de estudo",
    }
)
