"""Histórico de versões das partes e datas da composição (feature 016)."""

from datetime import datetime

from django import template

from sgp.core.formatting import local_datetime

register = template.Library()


@register.inclusion_tag("fulldoc/_part_history.html")
def historico_de_versoes(kind, obj):
    """Versões da parte (TAP, Plano de Negócios ou subdocumento) e do documento final (FR-008)."""
    from sgp.fulldoc import versioning

    if obj is None or getattr(obj, "pk", None) is None:
        return {"rows": []}
    return {"rows": versioning.part_history(kind, obj)}


@register.filter
def iso_datahora(value) -> str:
    """Data e hora ISO guardada na composição, no horário de Brasília."""
    if not value:
        return ""
    try:
        return local_datetime(datetime.fromisoformat(value))
    except (TypeError, ValueError):
        return str(value)
