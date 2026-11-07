"""Linhas derivadas (research R8): Verificação Final, pendências da Validação e marcos.

As linhas são copiadas no documento na criação e podem ser atualizadas a partir da Entrada
aprovada, preservando o que já foi preenchido em cada linha (pela referência da linha).
"""

from django.utils import timezone

from sgp.formtemplates import fieldtypes

from . import flow
from .models import ENTRY

FIXED_COLUMNS = {
    "entry_topics": [("label", "Requisito de entrada"), ("previsto", "Previsto")],
    "entry_requirements": [
        ("label", "Requisito"),
        ("criterio", "Critério de aceitação"),
        ("situacao", "Situação"),
    ],
    "milestones": [
        ("label", "Subdocumento"),
        ("planejado", "Planejado"),
        ("realizado", "Realizado"),
        ("situacao", "Situação"),
    ],
}


def topic_summary(topic_def: dict, topic_data: dict) -> str:
    if topic_data.get("na"):
        return f"Não aplicável: {topic_data.get('justification', '')}".strip()
    parts = []
    for field_def in topic_def.get("fields", []):
        text = fieldtypes.summary(field_def, topic_data.get("values", {}).get(field_def["key"]))
        if text:
            parts.append(f"{fieldtypes.label_of(field_def)}: {text}")
    return " | ".join(parts)


def _topic(topics: dict, key: str) -> dict:
    topic = topics.get(key) or {}
    return {
        "na": bool(topic.get("na")),
        "justification": topic.get("justification", ""),
        "values": topic.get("values", {}) or {},
    }


def _entry_rows(field_def: dict, entry) -> list[dict]:
    rows = []
    template, topics = flow.approved_content(entry) if entry else (None, {})
    for key in field_def.get("rows", []):
        topic_def = template.topic(key) if template else None
        if topic_def is None:
            rows.append(
                {
                    "ref": key,
                    "label": key,
                    "fixed": {"previsto": ""},
                    "values": {},
                    "editable": True,
                }
            )
            continue
        rows.append(
            {
                "ref": key,
                "label": topic_def.get("body_label") or topic_def["label"],
                "fixed": {"previsto": topic_summary(topic_def, _topic(topics, key))},
                "values": {},
                "editable": True,
            }
        )
    return rows


def _applicability(entry):
    template, topics = flow.approved_content(entry)
    for topic_def in template.topics:
        for field_def in topic_def.get("fields", []):
            if field_def["type"] == "applicability":
                values = _topic(topics, topic_def["key"]).get("values", {})
                return field_def, values.get(field_def["key"]) or []
    return None, []


def _requirement_rows(entry) -> list[dict]:
    if entry is None:
        return []
    field_def, rows = _applicability(entry)
    if field_def is None:
        return []
    labels = dict(fieldtypes.vocabulary_terms(field_def["vocabulary"]).values_list("code", "label"))
    result = []
    for row in rows:
        label = labels.get(row["codigo"], row["codigo"])
        if row.get("aplica") == "sim":
            result.append(
                {
                    "ref": row["codigo"],
                    "label": label,
                    "fixed": {"criterio": row.get("criterio", ""), "situacao": "Aplica"},
                    "values": {},
                    "editable": True,
                }
            )
        elif row.get("aplica") == "nao":
            result.append(
                {
                    "ref": row["codigo"],
                    "label": label,
                    "fixed": {
                        "criterio": "",
                        "situacao": f"Não se aplica: {row.get('justificativa', '')}",
                    },
                    "values": {},
                    "editable": False,
                }
            )
    return result


def _milestone_rows(project) -> list[dict]:
    today = timezone.localdate()
    rows = []
    for milestone in project.milestones.select_related("subdocument_type").order_by("planned_date"):
        if milestone.canceled_at:
            situation = "Cancelado"
        elif milestone.actual_date:
            situation = (
                "Concluído"
                if milestone.actual_date <= milestone.planned_date
                else "Concluído com atraso"
            )
        else:
            situation = "Atrasado" if milestone.planned_date < today else "No prazo"
        rows.append(
            {
                "ref": str(milestone.pk),
                "label": str(milestone),
                "fixed": {
                    "planejado": milestone.planned_date.strftime("%d/%m/%Y"),
                    "realizado": milestone.actual_date.strftime("%d/%m/%Y")
                    if milestone.actual_date
                    else "—",
                    "situacao": situation,
                },
                "values": {},
                "editable": False,
            }
        )
    return rows


def build_rows(field_def: dict, project) -> list[dict]:
    source = field_def["source"]
    if source == "milestones":
        return _milestone_rows(project)
    entry = flow.approved(project, ENTRY)
    if source == "entry_topics":
        return _entry_rows(field_def, entry)
    return _requirement_rows(entry)


def merge(new_rows: list[dict], old_value) -> dict:
    """Linhas novas com os valores já preenchidos nas linhas de mesma referência."""
    old = {row.get("ref"): row.get("values", {}) for row in (old_value or {}).get("rows", [])}
    merged = []
    for row in new_rows:
        values = old.get(row["ref"], {}) if row.get("editable", True) else {}
        merged.append({**row, "values": dict(values)})
    return {"rows": merged}
