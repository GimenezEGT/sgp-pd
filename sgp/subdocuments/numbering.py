"""Numeração automática de tópicos e tabelas (FR-011 da feature 004; research R13)."""

from sgp.formtemplates import fieldtypes
from sgp.formtemplates.schema import numbered_topics


def visible_topics(subdocument) -> list[tuple]:
    """(número ou None, tópico) visíveis no órgão regulador do projeto."""
    return numbered_topics(subdocument.template.definition, subdocument.project.regulatory_body)


def table_numbers(subdocument) -> dict[tuple[str, str], str]:
    """{(tópico, campo): "Tabela 01"} para as tabelas com conteúdo, na ordem do documento."""
    numbers, count = {}, 0
    for _, topic in visible_topics(subdocument):
        data = subdocument.topic_data(topic["key"])
        if data["na"]:
            continue
        for field_def in topic.get("fields", []):
            if fieldtypes.has_table(field_def, data["values"].get(field_def["key"])):
                count += 1
                numbers[(topic["key"], field_def["key"])] = f"Tabela {count:02d}"
    return numbers
