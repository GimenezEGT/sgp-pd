"""Leitura do POST do formulário montado a partir do modelo (research R7)."""

from sgp.formtemplates import fieldtypes
from sgp.formtemplates.schema import DISPLAY_ONLY

from . import numbering


def topic_prefix(topic_key: str) -> str:
    return f"t__{topic_key}"


def field_prefix(topic_key: str, field_key: str) -> str:
    return f"t__{topic_key}__{field_key}"


def parse_post(subdocument, post, files, *, context_for):
    """Devolve (dados dos tópicos visíveis, anexos novos [(tópico, campo, arquivos)], erros)."""
    topics, uploads, errors = {}, [], []
    for _, topic in numbering.visible_topics(subdocument):
        key = topic["key"]
        previous = subdocument.topic_data(key)
        base = topic_prefix(key)
        values = {}
        for field_def in topic.get("fields", []):
            if field_def["type"] in DISPLAY_ONLY:
                continue
            prefix = field_prefix(key, field_def["key"])
            ctx = context_for(previous=previous["values"].get(field_def["key"]))
            value, field_errors = fieldtypes.parse(field_def, post, prefix, ctx)
            errors.extend(f"{topic['label']} › {message}" for message in field_errors)
            values[field_def["key"]] = value
            if field_def["type"] == "attachment":
                new_files = [item for item in files.getlist(f"{prefix}__novo") if item]
                if new_files:
                    uploads.append((key, field_def["key"], new_files))
        topics[key] = {
            "na": bool(topic.get("allow_not_applicable")) and post.get(f"{base}__na") == "1",
            "justification": (post.get(f"{base}__justificativa") or "").strip(),
            "values": values,
        }
    return {"topics": topics}, uploads, errors
