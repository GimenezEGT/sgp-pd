"""Eventos das listas controladas (contrato eventos-auditoria.md da feature 003)."""

from sgp.audit.event_types import register_many

register_many(
    {
        "vocab.term_created": "Termo incluído na lista",
        "vocab.term_updated": "Termo alterado na lista",
        "vocab.term_deactivated": "Termo desativado na lista",
        "vocab.term_reactivated": "Termo reativado na lista",
    }
)
