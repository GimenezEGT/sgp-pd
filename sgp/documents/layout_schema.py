"""Definição do modelo de layout (contrato modelo-layout.md da feature 006).

O esquema fecha as chaves e os limites; as regras semânticas conferem marcadores de texto e
códigos de tipo de subdocumento. Mensagens em português, apontando o campo do formulário.
"""

import copy
import re

from jsonschema import Draft202012Validator

DASH = chr(0x2013)
TARGET_SUBDOCUMENT = "subdocument"
VARIANTS = ("topics", "checklist", "sectors")
PLACEHOLDERS = ("titulo", "produto", "versao", "projeto")
FONTS = ("Calibri",)

DEFAULT_DEFINITION = {
    "page": {
        "margin_top_cm": 2.0,
        "margin_bottom_cm": 2.0,
        "margin_left_cm": 1.3,
        "margin_right_cm": 1.3,
    },
    "font": {"family": "Calibri", "body_pt": 11},
    "logo": {"width_cm": 12.84, "height_cm": 1.8},
    "cover": {
        "indent_cm": 2.44,
        "second_column_cm": 5.09,
        "title_pt": 24,
        "title_pt_by_type": {
            "rapd": 23,
            "analise-critica": 23,
            "validacao": 23,
            "verificacao-final": 23,
            "saida": 23,
        },
        "variant_by_type": {"verificacao-final": "checklist", "saida": "sectors"},
        "topics_pt_by_type": {"saida": 11},
        "product_pt": 20,
        "version_pt": 20,
        "contains_pt": 16,
        "topics_pt": 14,
        "signature_pt": 12,
        "checklist_header_pt": 11,
    },
    "header": {"text": f"{{titulo}} {DASH} {{produto}} {DASH} Versão {{versao}}", "pt": 9},
    "footer": {"text": "", "pt": 11},
    "body": {"heading_pt": 12, "table_pt": 10, "table_header_fill": "#D9D9D9"},
    "watermark": {"text": f"RASCUNHO {DASH} NÃO VÁLIDO", "pt": 54, "color": "#D0D0D0"},
}


def default_definition(target: str) -> dict:
    definition = copy.deepcopy(DEFAULT_DEFINITION)
    if target != TARGET_SUBDOCUMENT:
        definition["cover"]["title_pt_by_type"] = {}
        definition["cover"]["variant_by_type"] = {}
        definition["cover"]["topics_pt_by_type"] = {}
    return definition


def _number(minimum, maximum):
    return {"type": "number", "minimum": minimum, "maximum": maximum}


PT = _number(6, 40)
MARGIN = _number(0.5, 4.0)
COLOR = {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"}
TEXT = {"type": "string", "maxLength": 300}


OPTIONAL = ("title_pt_by_type", "variant_by_type", "topics_pt_by_type")


def _object(properties: dict) -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [name for name in properties if name not in OPTIONAL],
        "properties": properties,
    }


SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    **_object(
        {
            "page": _object(
                {
                    "margin_top_cm": MARGIN,
                    "margin_bottom_cm": MARGIN,
                    "margin_left_cm": MARGIN,
                    "margin_right_cm": MARGIN,
                }
            ),
            "font": _object({"family": {"enum": list(FONTS)}, "body_pt": PT}),
            "logo": _object({"width_cm": _number(2, 18), "height_cm": _number(0.5, 5)}),
            "cover": _object(
                {
                    "indent_cm": _number(0, 8),
                    "second_column_cm": _number(2, 12),
                    "title_pt": PT,
                    "title_pt_by_type": {"type": "object", "additionalProperties": PT},
                    "variant_by_type": {
                        "type": "object",
                        "additionalProperties": {"enum": list(VARIANTS)},
                    },
                    "topics_pt_by_type": {"type": "object", "additionalProperties": PT},
                    "product_pt": PT,
                    "version_pt": PT,
                    "contains_pt": PT,
                    "topics_pt": PT,
                    "signature_pt": PT,
                    "checklist_header_pt": PT,
                }
            ),
            "header": _object({"text": TEXT, "pt": PT}),
            "footer": _object({"text": TEXT, "pt": PT}),
            "body": _object({"heading_pt": PT, "table_pt": PT, "table_header_fill": COLOR}),
            "watermark": _object(
                {
                    "text": {"type": "string", "minLength": 1, "maxLength": 60},
                    "pt": _number(20, 120),
                    "color": COLOR,
                }
            ),
        }
    ),
}

VALIDATOR = Draft202012Validator(SCHEMA)

SECTION_LABELS = {
    "page": "página",
    "font": "fonte",
    "logo": "logotipo",
    "cover": "capa",
    "header": "cabeçalho",
    "footer": "rodapé",
    "body": "corpo",
    "watermark": "marca d'água",
}
FIELD_LABELS = {
    "margin_top_cm": "margem superior (cm)",
    "margin_bottom_cm": "margem inferior (cm)",
    "margin_left_cm": "margem esquerda (cm)",
    "margin_right_cm": "margem direita (cm)",
    "family": "família",
    "body_pt": "tamanho do texto (pt)",
    "width_cm": "largura (cm)",
    "height_cm": "altura (cm)",
    "indent_cm": "recuo do conteúdo (cm)",
    "second_column_cm": "distância da segunda coluna de tópicos (cm)",
    "title_pt": "tamanho do título (pt)",
    "title_pt_by_type": "tamanho do título por tipo (pt)",
    "variant_by_type": "variante de capa por tipo",
    "topics_pt_by_type": "tamanho dos tópicos por tipo (pt)",
    "product_pt": "tamanho do nome do produto (pt)",
    "version_pt": "tamanho da versão (pt)",
    "contains_pt": "tamanho de 'ESTE RELATÓRIO DEVE CONTER' (pt)",
    "topics_pt": "tamanho dos tópicos (pt)",
    "signature_pt": "tamanho do bloco de assinaturas (pt)",
    "checklist_header_pt": "tamanho do cabeçalho da CHECK LIST (pt)",
    "text": "texto",
    "pt": "tamanho (pt)",
    "heading_pt": "tamanho dos títulos de tópico (pt)",
    "table_pt": "tamanho do texto das tabelas (pt)",
    "table_header_fill": "cor do cabeçalho das tabelas",
    "color": "cor",
}


def _where(path) -> str:
    parts = [str(part) for part in path]
    if not parts:
        return "definição"
    names = [SECTION_LABELS.get(parts[0], parts[0])]
    if len(parts) > 1:
        names.append(FIELD_LABELS.get(parts[1], parts[1]))
    if len(parts) > 2:
        names.append(parts[2])
    return " › ".join(names)


def schema_errors(definition) -> list[str]:
    if not isinstance(definition, dict):
        return ["A definição do layout precisa ser um objeto com as seções do modelo."]
    errors = []
    for error in sorted(VALIDATOR.iter_errors(definition), key=lambda e: list(e.path)):
        where = _where(error.path)
        if error.validator == "required":
            missing = error.message.split("'")[1] if "'" in error.message else ""
            label = FIELD_LABELS.get(missing, SECTION_LABELS.get(missing, missing))
            errors.append(f"{where}: falta {label}.")
        elif error.validator == "additionalProperties":
            errors.append(f"{where}: há campo desconhecido.")
        elif error.validator in ("minimum", "maximum"):
            errors.append(f"{where}: valor fora do limite permitido.")
        elif error.validator == "pattern":
            errors.append(f"{where}: use a cor no formato #RRGGBB.")
        elif error.validator == "enum":
            errors.append(f"{where}: valor não permitido.")
        elif error.validator == "minLength":
            errors.append(f"{where}: preencha o texto.")
        else:
            errors.append(f"{where}: valor inválido.")
    return errors


def placeholders(text: str) -> set[str]:
    return set(re.findall(r"\{([^{}]*)\}", text or ""))


def semantic_errors(definition: dict, *, target: str, type_codes=None) -> list[str]:
    errors = []
    for section in ("header", "footer"):
        unknown = placeholders(definition[section]["text"]) - set(PLACEHOLDERS)
        if unknown:
            allowed = ", ".join("{" + name + "}" for name in PLACEHOLDERS)
            errors.append(
                f"{SECTION_LABELS[section]} › texto: marcador desconhecido "
                f"{', '.join('{' + name + '}' for name in sorted(unknown))}; use {allowed}."
            )
    cover = definition["cover"]
    by_type = (
        set(cover.get("title_pt_by_type", {}))
        | set(cover.get("variant_by_type", {}))
        | set(cover.get("topics_pt_by_type", {}))
    )
    if target != TARGET_SUBDOCUMENT and by_type:
        errors.append("capa: tamanho e variante por tipo valem só no layout de subdocumentos.")
    elif type_codes is not None:
        unknown = by_type - set(type_codes)
        if unknown:
            errors.append(
                "capa: tipo de subdocumento inexistente ou inativo: "
                + ", ".join(sorted(unknown))
                + "."
            )
    return errors


def validate_definition(definition, *, target: str, type_codes=None) -> list[str]:
    errors = schema_errors(definition)
    if errors:
        return errors
    return semantic_errors(definition, target=target, type_codes=type_codes)


def fill(text: str, values: dict) -> str:
    """Troca os marcadores conhecidos ({titulo}, {produto}, {versao}, {projeto})."""
    return re.sub(
        r"\{(titulo|produto|versao|projeto)\}", lambda m: str(values.get(m.group(1), "")), text
    )
