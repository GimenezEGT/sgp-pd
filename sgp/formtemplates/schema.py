"""JSON Schema próprio da definição dos modelos de formulário e regras semânticas (feature 004).

O formato está em specs/004-modelos-subdocumentos/contracts/definicao-modelo.md. A definição é
conferida pelo schema (estrutura e tipos) e por regras que o schema não expressa: chaves e
rótulos únicos, listas controladas existentes e tópicos da Entrada usados nas linhas derivadas.
"""

from jsonschema import Draft202012Validator

FIELD_TYPES = (
    "rich_text",
    "text",
    "list",
    "table",
    "vocabulary",
    "reference",
    "attachment",
    "date",
    "number",
    "applicability",
    "derived_table",
    "entry_topics",
    "subdocuments",
    "lots_production",
    "note",
)
DISPLAY_ONLY = ("lots_production", "note")
COLUMN_TYPES = ("text", "number", "date", "reference", "vocabulary")
REFERENCE_KINDS = ("lotes", "insumos", "kits", "amostras", "paineis", "normas", "referencias")
# Cadastros com código único, aceitos em células de tabela (o código digitado é resolvido).
CODE_KINDS = ("lotes", "insumos", "amostras", "paineis", "normas")
DERIVED_SOURCES = ("entry_topics", "entry_requirements", "milestones")
PREFILLS = (
    "project.product_name",
    "project.title",
    "project.classification_rule",
    "project.risk_class",
)

KEY = {"type": "string", "pattern": "^[a-z][a-z0-9_]{0,39}$"}
LABEL = {"type": "string", "minLength": 1, "maxLength": 300}
TEXT = {"type": "string", "maxLength": 2000}
VOCAB_CODE = {"type": "string", "pattern": "^[a-z0-9-]{1,60}$"}


def _requires(type_name: str, *names: str) -> dict:
    return {
        "if": {"properties": {"type": {"const": type_name}}, "required": ["type"]},
        "then": {"required": list(names)},
    }


COLUMN = {
    "type": "object",
    "required": ["key", "label", "type"],
    "additionalProperties": False,
    "properties": {
        "key": KEY,
        "label": LABEL,
        "type": {"enum": list(COLUMN_TYPES)},
        "kind": {"enum": list(CODE_KINDS)},
        "vocabulary": VOCAB_CODE,
        "required": {"type": "boolean"},
        "sum": {"type": "boolean"},
        "decimals": {"type": "integer", "minimum": 0, "maximum": 6},
    },
    "allOf": [_requires("reference", "kind"), _requires("vocabulary", "vocabulary")],
}

FIELD = {
    "type": "object",
    "required": ["key", "type"],
    "additionalProperties": False,
    "properties": {
        "key": KEY,
        "type": {"enum": list(FIELD_TYPES)},
        "label": {"type": "string", "maxLength": 300},
        "help": {"type": "string", "maxLength": 500},
        "required": {"type": "boolean"},
        "multiple": {"type": "boolean"},
        "vocabulary": VOCAB_CODE,
        "kind": {"enum": list(REFERENCE_KINDS)},
        "filter": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "material_type": {"enum": ["raw", "packaging"]},
                "new_to_company": {"type": "boolean"},
            },
        },
        "columns": {"type": "array", "items": COLUMN},
        "source": {"enum": list(DERIVED_SOURCES)},
        "rows": {"type": "array", "items": KEY, "minItems": 1},
        "justify_unless": {
            "type": "object",
            "required": ["column", "value", "justification"],
            "additionalProperties": False,
            "properties": {"column": KEY, "value": {"type": "string"}, "justification": KEY},
        },
        "source_field": {"type": "string", "pattern": "^[a-z][a-z0-9_]*\\.[a-z][a-z0-9_]*$"},
        "text": TEXT,
        "prefill": {"enum": list(PREFILLS)},
        "decimals": {"type": "integer", "minimum": 0, "maximum": 6},
    },
    "allOf": [
        _requires("table", "columns"),
        _requires("vocabulary", "vocabulary"),
        _requires("applicability", "vocabulary"),
        _requires("reference", "kind"),
        _requires("derived_table", "source"),
        _requires("lots_production", "source_field"),
        _requires("note", "text"),
    ],
}

TOPIC = {
    "type": "object",
    "required": ["key", "label", "fields"],
    "additionalProperties": False,
    "properties": {
        "key": KEY,
        "label": LABEL,
        "body_label": {"type": "string", "maxLength": 300},
        "in_cover": {"type": "boolean"},
        "allow_not_applicable": {"type": "boolean"},
        "regulatory_body": {"enum": ["", "ANVISA", "MAPA"]},
        "help": {"type": "string", "maxLength": 1000},
        "require_any": {"type": "array", "items": KEY, "minItems": 2},
        "inherit": {
            "type": "object",
            "required": ["subdocument", "topic"],
            "additionalProperties": False,
            "properties": {"subdocument": VOCAB_CODE, "topic": KEY},
        },
        "fields": {"type": "array", "items": FIELD},
    },
}

DEFINITION_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["cover", "topics"],
    "additionalProperties": False,
    "properties": {
        "cover": {
            "type": "object",
            "required": ["title"],
            "additionalProperties": False,
            "properties": {
                "title": LABEL,
                "columns": {"enum": [1, 2]},
                "approver_label": {"type": "string", "maxLength": 200},
                "change_versions": {"type": "boolean"},
            },
        },
        "topics": {"type": "array", "items": TOPIC, "minItems": 1},
    },
}

VALIDATOR = Draft202012Validator(DEFINITION_SCHEMA)


def _where(definition: dict, path) -> str:
    """Traduz o caminho do erro para 'tópico N (rótulo) › campo chave'."""
    parts = list(path)
    text = []
    if len(parts) >= 2 and parts[0] == "topics" and isinstance(parts[1], int):
        topics = definition.get("topics") or []
        topic = topics[parts[1]] if parts[1] < len(topics) else {}
        label = topic.get("label", "") if isinstance(topic, dict) else ""
        text.append(f"tópico {parts[1] + 1}" + (f" ({label})" if label else ""))
        if len(parts) >= 4 and parts[2] == "fields" and isinstance(parts[3], int):
            fields = topic.get("fields") or [] if isinstance(topic, dict) else []
            field = fields[parts[3]] if parts[3] < len(fields) else {}
            key = field.get("key", "") if isinstance(field, dict) else ""
            text.append(f"campo {parts[3] + 1}" + (f" ({key})" if key else ""))
    elif parts and parts[0] == "cover":
        text.append("capa")
    return " › ".join(text) or "definição"


def schema_errors(definition) -> list[str]:
    if not isinstance(definition, dict):
        return ["A definição precisa ser um objeto JSON com 'cover' e 'topics'."]
    errors = []
    for error in sorted(VALIDATOR.iter_errors(definition), key=lambda e: list(e.path)):
        errors.append(f"{_where(definition, error.path)}: {error.message}")
    return errors


def semantic_errors(definition: dict, *, vocabularies=None, entry_topic_keys=None) -> list[str]:
    """Regras que o schema não expressa. `vocabularies`: códigos existentes; `entry_topic_keys`:
    chaves dos tópicos da Entrada vigente (para `rows` de linhas derivadas)."""
    errors = []
    topic_keys, labels = set(), set()
    for index, topic in enumerate(definition.get("topics", []), start=1):
        name = f"tópico {index} ({topic.get('label', '')})"
        key = topic.get("key")
        if key in topic_keys:
            errors.append(f"{name}: chave {key!r} repetida no modelo.")
        topic_keys.add(key)
        label = " ".join(str(topic.get("label", "")).split()).lower()
        if label in labels:
            errors.append(
                f"{name}: rótulo repetido no modelo; cada tópico precisa de rótulo único."
            )
        labels.add(label)
        field_keys = set()
        for field in topic.get("fields", []):
            fkey = field.get("key")
            if fkey in field_keys:
                errors.append(f"{name}: campo {fkey!r} repetido no tópico.")
            field_keys.add(fkey)
            columns = [column.get("key") for column in field.get("columns", [])]
            if len(columns) != len(set(columns)):
                errors.append(f"{name}: coluna repetida no campo {fkey!r}.")
            codes = [field.get("vocabulary")] + [
                column.get("vocabulary") for column in field.get("columns", [])
            ]
            for code in filter(None, codes):
                if vocabularies is not None and code not in vocabularies:
                    errors.append(f"{name}: lista controlada {code!r} não existe.")
            if field.get("type") == "derived_table" and field.get("source") == "entry_topics":
                missing = [
                    row
                    for row in field.get("rows", [])
                    if entry_topic_keys is not None and row not in entry_topic_keys
                ]
                if not field.get("rows"):
                    errors.append(f"{name}: linhas derivadas da Entrada precisam de 'rows'.")
                if missing:
                    errors.append(
                        f"{name}: tópicos da Entrada inexistentes em 'rows': {', '.join(missing)}."
                    )
            justify = field.get("justify_unless")
            if justify:
                keys = set(columns)
                if justify["column"] not in keys or justify["justification"] not in keys:
                    errors.append(f"{name}: 'justify_unless' cita coluna inexistente.")
        for required_key in topic.get("require_any", []):
            if required_key not in field_keys:
                errors.append(f"{name}: 'require_any' cita campo inexistente {required_key!r}.")
    for topic in definition.get("topics", []):
        for field in topic.get("fields", []):
            source = field.get("source_field")
            if source:
                source_topic, source_key = source.split(".", 1)
                found = any(
                    other.get("key") == source_topic
                    and any(f.get("key") == source_key for f in other.get("fields", []))
                    for other in definition.get("topics", [])
                )
                if not found:
                    errors.append(
                        f"campo {field.get('key')!r}: 'source_field' {source!r} não existe."
                    )
    return errors


def validate_definition(definition, *, vocabularies=None, entry_topic_keys=None) -> list[str]:
    errors = schema_errors(definition)
    if errors:
        return errors
    return semantic_errors(definition, vocabularies=vocabularies, entry_topic_keys=entry_topic_keys)


def numbered_topics(definition: dict, regulatory_body: str | None = None) -> list[tuple]:
    """(número ou None, tópico) na ordem; só tópicos da capa e visíveis no órgão recebem número."""
    result, number = [], 0
    for topic in definition.get("topics", []):
        body = topic.get("regulatory_body") or ""
        visible = not body or regulatory_body is None or body == regulatory_body
        if not visible:
            continue
        if topic.get("in_cover", True):
            number += 1
            result.append((number, topic))
        else:
            result.append((None, topic))
    return result
