"""Monta, a partir do modelo usado, o que as telas mostram e editam (research R7 e R12)."""

from urllib.parse import urlencode

from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe

from sgp.catalog.kinds import get_kind
from sgp.files.models import StoredFile
from sgp.formtemplates import fieldtypes

from . import derived, numbering, parsing
from .models import Subdocument

BLANK_ROWS = 2
OPTIONAL_FORM = "formulario_opcional"


def rich_text(text: str):
    """Parágrafos e listas simples ("- "), sempre escapados (sem HTML do usuário)."""
    html, items = [], []
    for block in (text or "").replace("\r\n", "\n").split("\n\n"):
        lines = [line for line in block.split("\n") if line.strip()]
        if not lines:
            continue
        if all(line.lstrip().startswith("- ") for line in lines):
            items = "".join(f"<li>{escape(line.lstrip()[2:])}</li>" for line in lines)
            html.append(f"<ul>{items}</ul>")
        else:
            html.append("<p>" + "<br>".join(escape(line) for line in lines) + "</p>")
    return mark_safe("".join(html))  # noqa: S308 - conteúdo escapado acima


def _options(vocabulary: str, selected) -> list[dict]:
    selected = selected if isinstance(selected, list) else [selected] if selected else []
    terms = fieldtypes.vocabulary_terms(vocabulary).order_by("position", "label")
    return [
        {"value": term.code, "label": term.label, "selected": term.code in selected}
        for term in terms
        if term.is_active or term.code in selected
    ]


def _cell_input(column: dict, value) -> str:
    if value in (None, ""):
        return ""
    if column["type"] == "number":
        return fieldtypes.display_number(value, column.get("decimals"))
    if column["type"] == "reference":
        return value.get("code", "") if isinstance(value, dict) else str(value)
    return str(value)


def _table(field_def, value, name, editing):
    columns = []
    for column in field_def["columns"]:
        item = dict(column)
        if column["type"] == "vocabulary":
            item["choices"] = _options(column["vocabulary"], None)
        columns.append(item)
    rows = []
    for index, row in enumerate(value or []):
        cells = []
        for column in columns:
            cell = row.get(column["key"])
            cells.append(
                {
                    "name": f"{name}__{index}__{column['key']}",
                    "input": _cell_input(column, cell),
                    "text": fieldtypes.cell_text(column, cell),
                    "column": column,
                }
            )
        rows.append(cells)
    blanks = []
    if editing:
        start = len(rows)
        for index in range(start, start + BLANK_ROWS):
            blanks.append(
                [
                    {
                        "name": f"{name}__{index}__{column['key']}",
                        "input": "",
                        "text": "",
                        "column": column,
                    }
                    for column in columns
                ]
            )
    totals = [
        fieldtypes.column_total(field_def, value, column["key"]) if column.get("sum") else None
        for column in columns
    ]
    return {
        "columns": columns,
        "rows": rows,
        "blanks": blanks,
        "totals": totals if any(totals) else None,
    }


def blank_row(field_def: dict, name: str, index: int) -> list[dict]:
    view = _table(field_def, [], name, editing=False)
    return [
        {"name": f"{name}__{index}__{column['key']}", "input": "", "text": "", "column": column}
        for column in view["columns"]
    ]


def _references(field_def, value, name, subdocument):
    ids = value if isinstance(value, list) else [value] if value else []
    kind = get_kind(field_def["kind"])
    records = {record.pk: record for record in kind.model.objects.filter(pk__in=ids)}
    params = {"campo": name}
    if kind.project_scoped:
        params["projeto"] = subdocument.project_id
    for key, item in (field_def.get("filter") or {}).items():
        params["tipo_insumo" if key == "material_type" else "novo"] = (
            item if key == "material_type" else ("1" if item else "0")
        )
    return {
        "selected": [records[pk] for pk in ids if pk in records],
        "kind": kind,
        "search_url": reverse("catalog:search", args=[kind.slug]) + "?" + urlencode(params),
    }


def _applicability(field_def, value):
    current = {row["codigo"]: row for row in value or []}
    rows = []
    for term in fieldtypes.vocabulary_terms(field_def["vocabulary"]).order_by("position"):
        row = current.get(term.code, {})
        if not term.is_active and not row:
            continue
        rows.append(
            {
                "code": term.code,
                "label": term.label,
                "aplica": row.get("aplica", ""),
                "criterio": row.get("criterio", ""),
                "justificativa": row.get("justificativa", ""),
            }
        )
    return rows


def _derived(field_def, value):
    fixed = derived.FIXED_COLUMNS[field_def["source"]]
    columns = []
    for column in field_def.get("columns", []):
        item = dict(column)
        if column["type"] == "vocabulary":
            item["choices"] = _options(column["vocabulary"], None)
        columns.append(item)
    rows = []
    required = [column["key"] for column in columns if column.get("required")]
    for row in (value or {}).get("rows", []):
        fixed_values = dict(row.get("fixed", {}))
        if field_def["source"] == "entry_requirements" and row.get("editable", True) and required:
            # Pendência da Validação (FR-018): cumprida quando a evidência está registrada.
            done = all(row.get("values", {}).get(key) for key in required)
            fixed_values["situacao"] = "Aplica – cumprida" if done else "Aplica – pendente"
        fixed_cells = [row.get("label", "")] + [fixed_values.get(key, "") for key, _ in fixed[1:]]
        cells = []
        for column in columns:
            raw = row.get("values", {}).get(column["key"], "")
            cells.append(
                {
                    "column": column,
                    "input": raw,
                    "text": fieldtypes.term_labels(column["vocabulary"], raw)[0]
                    if column["type"] == "vocabulary" and raw
                    else raw,
                }
            )
        rows.append({"fixed": fixed_cells, "cells": cells, "editable": row.get("editable", True)})
    return {"fixed_headers": [label for _, label in fixed], "columns": columns, "rows": rows}


def _lots_production(field_def, subdocument):
    topic_key, field_key = field_def["source_field"].split(".", 1)
    ids = subdocument.topic_data(topic_key)["values"].get(field_key) or []
    ids = ids if isinstance(ids, list) else [ids]
    lots = (
        get_kind("lotes").model.objects.filter(pk__in=ids).select_related("production_responsible")
    )
    return [
        f"{lot.display} – responsável: {lot.production_responsible.get_full_name()} – local: {lot.manufacturing_site}"
        for lot in lots
    ]


def field_view(
    field_def: dict,
    value,
    *,
    name: str,
    subdocument: Subdocument,
    editing: bool,
    entry_labels: dict,
):
    kind = field_def["type"]
    view = {
        "def": field_def,
        "type": kind,
        "name": name,
        "label": fieldtypes.label_of(field_def),
        "help": field_def.get("help", ""),
        "required": field_def.get("required", False),
        "value": value,
        "empty": fieldtypes.is_empty(field_def, value),
    }
    if kind == "rich_text":
        view["html"] = rich_text(value)
    elif kind == "list":
        view["text"] = "\n".join(value or [])
    elif kind == "vocabulary":
        view["choices"] = _options(field_def["vocabulary"], value)
        view["text"] = "; ".join(fieldtypes.term_labels(field_def["vocabulary"], value))
    elif kind == "reference":
        view.update(_references(field_def, value, name, subdocument))
    elif kind == "attachment":
        view["files"] = list(StoredFile.objects.filter(pk__in=value or []))
    elif kind == "date":
        view["text"] = fieldtypes.display_date(value)
    elif kind == "number":
        view["text"] = fieldtypes.display_number(value, field_def.get("decimals"))
    elif kind == "table":
        view["table"] = _table(field_def, value, name, editing)
    elif kind == "applicability":
        view["requirements"] = _applicability(field_def, value)
    elif kind == "derived_table":
        view["derived"] = _derived(field_def, value)
    elif kind == "entry_topics":
        selected = value or []
        view["choices"] = [
            {"value": key, "label": label, "selected": key in selected}
            for key, label in entry_labels.items()
        ]
        view["text"] = "; ".join(entry_labels.get(key, key) for key in selected)
    elif kind == "subdocuments":
        selected = value or []
        others = Subdocument.objects.filter(project=subdocument.project).exclude(pk=subdocument.pk)
        view["choices"] = [
            {"value": other.pk, "label": str(other), "selected": other.pk in selected}
            for other in others.select_related("subdocument_type")
        ]
        view["text"] = "; ".join(
            choice["label"] for choice in view["choices"] if choice["selected"]
        )
    elif kind == "lots_production":
        view["lines"] = _lots_production(field_def, subdocument)
    elif kind == "note":
        view["text"] = field_def.get("text", "")
    return view


def topics_view(
    subdocument: Subdocument, *, data: dict | None = None, editing: bool = False, entry_labels=None
):
    """Tópicos visíveis com número, dados e campos prontos para o template."""
    from . import services

    entry_labels = (
        entry_labels if entry_labels is not None else services.entry_topics(subdocument.project)[1]
    )
    tables = numbering.table_numbers(subdocument)
    result = []
    for number, topic in numbering.visible_topics(subdocument):
        key = topic["key"]
        topic_data = (
            (data or {}).get("topics", {}).get(key) if data else None
        ) or subdocument.topic_data(key)
        fields = []
        for field_def in topic.get("fields", []):
            name = parsing.field_prefix(key, field_def["key"])
            item = field_view(
                field_def,
                topic_data.get("values", {}).get(field_def["key"]),
                name=name,
                subdocument=subdocument,
                editing=editing,
                entry_labels=entry_labels,
            )
            item["table_number"] = tables.get((key, field_def["key"]))
            fields.append(item)
        context_lines = []
        if key == OPTIONAL_FORM:
            # Formulário opcional (FR-017): nome do projeto e versão vêm do projeto e do documento.
            context_lines = [
                f"Nome do Projeto: {subdocument.project.title}",
                f"Versão: {subdocument.version_display}",
            ]
        result.append(
            {
                "context_lines": context_lines,
                "number": number,
                "key": key,
                "prefix": parsing.topic_prefix(key),
                "label": topic.get("body_label") or topic["label"],
                "help": topic.get("help", ""),
                "allow_na": topic.get("allow_not_applicable", False),
                "na": topic_data.get("na", False),
                "justification": topic_data.get("justification", ""),
                "inherited": bool(topic.get("inherit")),
                "fields": fields,
            }
        )
    return result
