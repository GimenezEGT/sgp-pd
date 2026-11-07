"""Mascaramento de campos sensíveis na apresentação da trilha (tela e exportação).

O valor gravado (e o hash) nunca muda; só a apresentação troca o valor por MASK para quem não
pode vê-lo. Cada app registra, por tipo de evento, as chaves sensíveis e a regra de visibilidade
`can_view(viewer, project_id, cache) -> bool`.
"""

from collections.abc import Callable

MASK = "[restrito]"

_RULES: dict[str, tuple[frozenset[str], Callable]] = {}


def register(event_type: str, keys, can_view: Callable) -> None:
    _RULES[event_type] = (frozenset(keys), can_view)


def mask_value(value, keys: frozenset[str]):
    if isinstance(value, dict):
        return {
            key: (MASK if key in keys else mask_value(item, keys)) for key, item in value.items()
        }
    if isinstance(value, list):
        return [mask_value(item, keys) for item in value]
    return value


def present(event, viewer, cache: dict | None = None) -> tuple:
    """Valores anterior e novo como o `viewer` pode vê-los."""
    rule = _RULES.get(event.event_type)
    if rule is None:
        return event.old_value, event.new_value
    keys, can_view = rule
    cache = {} if cache is None else cache
    if can_view(viewer, event.project_id, cache):
        return event.old_value, event.new_value
    return mask_value(event.old_value, keys), mask_value(event.new_value, keys)


def sensitive_event_types() -> set[str]:
    return set(_RULES)
