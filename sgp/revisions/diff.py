"""Comparação entre versões de modelo (FR-007, FR-018; research R6).

A definição é achatada em caminhos rotulados; listas de objetos com `key` são casadas pela chave
(tópicos, campos, colunas) e o restante pelo valor. Item incluído ou retirado aparece uma vez, sem
repetir o que há dentro dele.
"""

import json

from sgp.documents.layout_schema import FIELD_LABELS, SECTION_LABELS

ITEM = "__item__"
KEYED_NAMES = {"topics": "tópico", "fields": "campo", "columns": "coluna"}
NAMES = {
    "cover": "capa",
    "title": "título",
    "label": "rótulo",
    "body_label": "rótulo no corpo",
    "columns": "colunas",
    "approver_label": "rótulo do aprovador",
    "change_versions": "versões alterada e nova",
    "type": "tipo",
    "required": "obrigatório",
    "vocabulary": "lista",
    "help": "ajuda",
    "in_cover": "na capa",
    "allow_not_applicable": "aceita não aplicável",
    "regulatory_body": "órgão regulador",
    "rows": "linhas",
    "source": "origem",
    "text": "texto",
    "kind": "cadastro",
    "multiple": "múltipla escolha",
    **SECTION_LABELS,
    **FIELD_LABELS,
}


def _name(segment: str) -> str:
    return NAMES.get(segment, segment)


def _display(value) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def flatten(value, path=(), label=()) -> dict:
    """{caminho: (rótulo, valor)}; marca com ITEM cada objeto casado por chave."""
    out = {}
    if isinstance(value, dict):
        for key in sorted(value):
            out.update(flatten(value[key], path + (key,), label + (_name(key),)))
    elif (
        isinstance(value, list)
        and value
        and all(isinstance(item, dict) and "key" in item for item in value)
    ):
        kind = KEYED_NAMES.get(path[-1] if path else "", "item")
        for item in value:
            item_label = f"{kind} «{item.get('label') or item['key']}»"
            item_path = path + (f"[{item['key']}]",)
            item_labels = label[:-1] + (item_label,) if label else (item_label,)
            out[item_path + (ITEM,)] = (" › ".join(item_labels), item.get("label") or item["key"])
            out.update(
                flatten({k: v for k, v in item.items() if k != "key"}, item_path, item_labels)
            )
    else:
        out[path] = (" › ".join(label) or "definição", value)
    return out


def compare(old: dict, new: dict) -> dict:
    """{"added": [(rótulo, valor)], "removed": [(rótulo, valor)], "changed": [(rótulo, antes, depois)]}."""
    a, b = flatten(old), flatten(new)
    added_items = [p[:-1] for p in b if p[-1] == ITEM and p not in a]
    removed_items = [p[:-1] for p in a if p[-1] == ITEM and p not in b]

    def inside(path, items, strict=False):
        return any(
            path[: len(item)] == item and (not strict or len(path) > len(item)) for item in items
        )

    def keep(path, items):
        if path[-1] == ITEM:
            return not inside(path[:-1], items, strict=True)
        return not inside(path, items)

    added = [(b[p][0], _display(b[p][1])) for p in b if p not in a and keep(p, added_items)]
    removed = [(a[p][0], _display(a[p][1])) for p in a if p not in b and keep(p, removed_items)]
    changed = [
        (b[p][0], _display(a[p][1]), _display(b[p][1]))
        for p in b
        if p in a and p[-1] != ITEM and a[p][1] != b[p][1]
    ]
    return {"added": added, "removed": removed, "changed": changed}


def is_empty(result: dict) -> bool:
    return not (result["added"] or result["removed"] or result["changed"])
