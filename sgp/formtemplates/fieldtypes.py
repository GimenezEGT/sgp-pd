"""Tipos de campo dos modelos: leitura do formulário, validação, vazio, resumo e referências.

Cada função recebe a definição do campo (dicionário do modelo) e um contexto com o projeto, o
valor anterior e quem grava. Os valores gravados seguem specs/004-.../research.md (R6).
"""

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation

from sgp.core.formatting import format_decimal_br

BR_NUMBER = re.compile(r"^-?(\d{1,3}(\.\d{3})+|\d+)(,\d+)?$")
SUMMARY_LIMIT = 300
CODE_FIELDS = {
    "lotes": "code",
    "insumos": "code",
    "amostras": "identifier",
    "paineis": "code",
    "normas": "identifier",
}


@dataclass
class Context:
    """O que o tipo de campo precisa saber para ler e validar um valor."""

    project: object = None
    subdocument: object = None
    by: object = None
    previous: object = None
    files: list = field(default_factory=list)
    new_files: list = field(default_factory=list)
    entry_topic_keys: tuple = ()
    entry_topic_labels: dict = field(default_factory=dict)


# ------------------------------------------------------------------- utilidades


def parse_number(text: str):
    """'1.234,5' → Decimal('1234.5'); vírgula decimal e ponto de milhar (padrão brasileiro)."""
    text = (text or "").strip()
    if not text:
        return None
    if not BR_NUMBER.match(text):
        raise ValueError("Use vírgula para decimais e ponto só para milhar (ex.: 1.234,5).")
    try:
        return Decimal(text.replace(".", "").replace(",", "."))
    except InvalidOperation as exc:  # pragma: no cover - a expressão já filtra
        raise ValueError("Número inválido.") from exc


def number_text(value: Decimal | None) -> str:
    return "" if value is None else format(value.normalize(), "f")


def display_number(text, decimals=None) -> str:
    if text in (None, ""):
        return ""
    value = Decimal(str(text))
    places = decimals if decimals is not None else max(0, -value.as_tuple().exponent)
    return format_decimal_br(value, places)


def parse_date(text: str):
    text = (text or "").strip()
    if not text:
        return ""
    for pattern in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            from datetime import datetime

            return datetime.strptime(text, pattern).date().isoformat()
        except ValueError:
            continue
    raise ValueError("Data inválida (use dd/mm/aaaa).")


def display_date(text) -> str:
    if not text:
        return ""
    return date.fromisoformat(text).strftime("%d/%m/%Y")


def collapse(text: str, limit: int = SUMMARY_LIMIT) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def label_of(field_def: dict) -> str:
    return field_def.get("label") or field_def.get("key", "")


# ---------------------------------------------------------------- listas e cadastros


def vocabulary_terms(code: str):
    from sgp.vocab.models import Term

    return Term.objects.of(code)


def term_labels(code: str, values) -> list[str]:
    values = values if isinstance(values, list) else [values] if values else []
    labels = dict(vocabulary_terms(code).filter(code__in=values).values_list("code", "label"))
    return [labels.get(value, value) for value in values]


def catalog_kind(slug: str):
    from sgp.catalog.kinds import get_kind

    return get_kind(slug)


def reference_queryset(field_def: dict, ctx: Context):
    """Cadastros que podem ser escolhidos agora (vigentes, ativos, do projeto e do filtro)."""
    kind = catalog_kind(field_def["kind"])
    queryset = kind.model.objects.available()
    if kind.project_scoped:
        queryset = queryset.filter(project=ctx.project)
    for name, value in (field_def.get("filter") or {}).items():
        queryset = queryset.filter(**{name: value})
    return queryset


def reference_display(slug: str, ids) -> list[str]:
    ids = ids if isinstance(ids, list) else [ids] if ids else []
    model = catalog_kind(slug).model
    records = {record.pk: record for record in model.objects.filter(pk__in=ids)}
    return [str(records[pk]) if pk in records else f"registro {pk}" for pk in ids]


def resolve_code(column: dict, code: str, ctx: Context, previous_cell=None):
    """Código digitado numa célula → id da versão do cadastro (mantém a versão já escolhida)."""
    code = (code or "").strip()
    if not code:
        return None
    if isinstance(previous_cell, dict) and previous_cell.get("code") == code:
        return previous_cell
    kind = catalog_kind(column["kind"])
    queryset = kind.model.objects.available().filter(**{CODE_FIELDS[column["kind"]]: code})
    if kind.project_scoped:
        queryset = queryset.filter(project=ctx.project)
    record = queryset.first()
    if record is None:
        raise ValueError(f"{kind.label} {code} não encontrado entre os cadastros ativos.")
    return {"id": record.pk, "code": code}


# --------------------------------------------------------------------- leitura


def _getlist(post, name):
    return [value for value in post.getlist(name) if value != ""]


def parse(field_def: dict, post, prefix: str, ctx: Context):
    """Lê o valor do formulário; devolve (valor, erros)."""
    kind = field_def["type"]
    errors: list[str] = []
    label = label_of(field_def)
    if kind in ("rich_text", "text"):
        value = (post.get(prefix) or "").strip()
        if kind == "text" and len(value) > 500:
            errors.append(f"{label}: até 500 caracteres.")
        return value, errors
    if kind == "list":
        return [
            line.strip() for line in (post.get(prefix) or "").splitlines() if line.strip()
        ], errors
    if kind == "date":
        try:
            return parse_date(post.get(prefix)), errors
        except ValueError as exc:
            return "", [f"{label}: {exc}"]
    if kind == "number":
        try:
            return number_text(parse_number(post.get(prefix))), errors
        except ValueError as exc:
            return "", [f"{label}: {exc}"]
    if kind == "vocabulary":
        values = _getlist(post, prefix) if field_def.get("multiple") else (post.get(prefix) or "")
        return values, errors
    if kind == "reference":
        ids = []
        for raw in _getlist(post, prefix):
            if raw.isdigit() and int(raw) not in ids:
                ids.append(int(raw))
        return (ids if field_def.get("multiple", True) else (ids[0] if ids else None)), errors
    if kind == "attachment":
        previous = ctx.previous or []
        kept = [int(raw) for raw in _getlist(post, f"{prefix}__manter") if raw.isdigit()]
        kept = [pk for pk in previous if pk in kept]
        return kept, errors
    if kind in ("entry_topics",):
        return _getlist(post, prefix), errors
    if kind == "subdocuments":
        return [int(raw) for raw in _getlist(post, prefix) if raw.isdigit()], errors
    if kind == "table":
        return _parse_table(field_def, post, prefix, ctx, errors), errors
    if kind == "applicability":
        return _parse_applicability(field_def, post, prefix), errors
    if kind == "derived_table":
        return _parse_derived(field_def, post, prefix, ctx), errors
    return None, errors


def _parse_cell(column: dict, raw: str, ctx: Context, previous_cell, errors, label, row):
    kind = column["type"]
    try:
        if kind == "number":
            return number_text(parse_number(raw))
        if kind == "date":
            return parse_date(raw)
        if kind == "reference":
            return resolve_code(column, raw, ctx, previous_cell)
    except ValueError as exc:
        errors.append(f"{label}, linha {row}, {column['label']}: {exc}")
        return raw
    return (raw or "").strip()


def row_indexes(post, prefix: str) -> list[int]:
    """Índices de linha presentes no formulário (linhas novas do HTMX têm índices grandes)."""
    start = f"{prefix}__"
    found = set()
    for name in post:
        if name.startswith(start):
            head = name[len(start) :].split("__", 1)[0]
            if head.isdigit():
                found.add(int(head))
    return sorted(found)[:2000]


def _parse_table(field_def, post, prefix, ctx, errors):
    previous = ctx.previous if isinstance(ctx.previous, list) else []
    rows = []
    for index in row_indexes(post, prefix):
        raw = {
            col["key"]: post.get(f"{prefix}__{index}__{col['key']}", "")
            for col in field_def["columns"]
        }
        if not any(str(value).strip() for value in raw.values()):
            continue
        old_row = previous[index] if index < len(previous) else {}
        row = {}
        for column in field_def["columns"]:
            row[column["key"]] = _parse_cell(
                column,
                raw[column["key"]],
                ctx,
                old_row.get(column["key"]) if isinstance(old_row, dict) else None,
                errors,
                label_of(field_def),
                len(rows) + 1,
            )
        rows.append(row)
    return rows


def _parse_applicability(field_def, post, prefix):
    rows = []
    for term in vocabulary_terms(field_def["vocabulary"]).order_by("position"):
        base = f"{prefix}__{term.code}"
        rows.append(
            {
                "codigo": term.code,
                "aplica": post.get(f"{base}__aplica", ""),
                "criterio": (post.get(f"{base}__criterio") or "").strip(),
                "justificativa": (post.get(f"{base}__justificativa") or "").strip(),
            }
        )
    return rows


def _parse_derived(field_def, post, prefix, ctx):
    previous = ctx.previous if isinstance(ctx.previous, dict) else {"rows": []}
    rows = []
    for index, row in enumerate(previous.get("rows", [])):
        values = dict(row.get("values", {}))
        if row.get("editable", True):
            for column in field_def.get("columns", []):
                name = f"{prefix}__{index}__{column['key']}"
                if name in post:
                    values[column["key"]] = (post.get(name) or "").strip()
        rows.append({**row, "values": values})
    return {"rows": rows}


# ------------------------------------------------------------------ validação


def validate(field_def: dict, value, ctx: Context) -> list[str]:
    """Formato e coerência do valor gravado (rascunho pode ficar incompleto)."""
    kind = field_def["type"]
    label = label_of(field_def)
    errors = []
    if kind == "vocabulary" and value:
        values = value if isinstance(value, list) else [value]
        terms = dict(
            vocabulary_terms(field_def["vocabulary"])
            .filter(code__in=values)
            .values_list("code", "is_active")
        )
        previous = (
            ctx.previous
            if isinstance(ctx.previous, list)
            else [ctx.previous]
            if ctx.previous
            else []
        )
        for code in values:
            if code not in terms or (not terms[code] and code not in previous):
                errors.append(f"{label}: opção inválida {code!r}.")
    elif kind == "reference" and value:
        ids = value if isinstance(value, list) else [value]
        previous = (
            ctx.previous
            if isinstance(ctx.previous, list)
            else [ctx.previous]
            if ctx.previous
            else []
        )
        allowed = set(
            reference_queryset(field_def, ctx).filter(pk__in=ids).values_list("pk", flat=True)
        )
        for pk in ids:
            if pk not in allowed and pk not in previous:
                errors.append(f"{label}: cadastro {pk} não pode ser escolhido aqui.")
    elif kind == "applicability":
        for row in value or []:
            if row.get("aplica") not in ("", "sim", "nao"):
                errors.append(f"{label}: escolha 'aplica' ou 'não se aplica'.")
            if row.get("aplica") == "nao" and not row.get("justificativa"):
                errors.append(
                    f"{label}: requisito {term_labels(field_def['vocabulary'], row['codigo'])[0]} "
                    "marcado 'não se aplica' exige justificativa."
                )
    elif kind == "derived_table" and value:
        rule = field_def.get("justify_unless")
        for number, row in enumerate(value.get("rows", []), start=1):
            values = row.get("values", {})
            for column in field_def.get("columns", []):
                if column["type"] == "vocabulary" and values.get(column["key"]):
                    codes = set(
                        vocabulary_terms(column["vocabulary"]).values_list("code", flat=True)
                    )
                    if values[column["key"]] not in codes:
                        errors.append(f"{label}, linha {number}: opção inválida.")
            if rule and values.get(rule["column"]) and values.get(rule["column"]) != rule["value"]:
                if not values.get(rule["justification"]):
                    errors.append(
                        f"{label}, linha {number} ({row.get('label', '')}): disposição diferente de "
                        "Aprovado exige justificativa."
                    )
    elif kind == "entry_topics" and value:
        unknown = [key for key in value if ctx.entry_topic_keys and key not in ctx.entry_topic_keys]
        if unknown:
            errors.append(f"{label}: tópicos inexistentes na Entrada: {', '.join(unknown)}.")
    elif kind == "subdocuments" and value:
        from sgp.subdocuments.models import Subdocument

        valid = set(
            Subdocument.objects.filter(project=ctx.project, pk__in=value).values_list(
                "pk", flat=True
            )
        )
        if ctx.subdocument is not None:
            valid.discard(ctx.subdocument.pk)
        if any(pk not in valid for pk in value):
            errors.append(f"{label}: escolha subdocumentos deste projeto.")
    return errors


def is_empty(field_def: dict, value) -> bool:
    kind = field_def["type"]
    if kind in ("note", "lots_production"):
        return True
    if kind == "applicability":
        return not any(row.get("aplica") for row in value or [])
    if kind == "derived_table":
        return not any(
            any(str(item).strip() for item in row.get("values", {}).values())
            for row in (value or {}).get("rows", [])
        )
    if isinstance(value, list | dict | str):
        return len(value) == 0
    return value is None


def incomplete(field_def: dict, value) -> list[str]:
    """O que falta para aprovar (obrigatórios e colunas obrigatórias)."""
    label = label_of(field_def)
    missing = []
    kind = field_def["type"]
    if field_def.get("required") and is_empty(field_def, value):
        missing.append(f"{label}: obrigatório.")
    if kind == "applicability" and field_def.get("required"):
        for row in value or []:
            if not row.get("aplica"):
                missing.append(
                    f"{label}: marque 'aplica' ou 'não se aplica' em "
                    f"{term_labels(field_def['vocabulary'], row['codigo'])[0]}."
                )
    if kind == "derived_table":
        required = [column for column in field_def.get("columns", []) if column.get("required")]
        for number, row in enumerate((value or {}).get("rows", []), start=1):
            if not row.get("editable", True):
                continue
            for column in required:
                if not row.get("values", {}).get(column["key"]):
                    missing.append(f"{label}, linha {number}: {column['label']} obrigatório.")
    if kind == "table":
        required = [column for column in field_def.get("columns", []) if column.get("required")]
        for number, row in enumerate(value or [], start=1):
            for column in required:
                if row.get(column["key"]) in (None, ""):
                    missing.append(f"{label}, linha {number}: {column['label']} obrigatório.")
    return missing


# --------------------------------------------------------- resumo e referências


def summary(field_def: dict, value) -> str:
    """Texto curto do valor (usado no "Previsto" da Verificação Final)."""
    kind = field_def["type"]
    if is_empty(field_def, value):
        return ""
    if kind in ("rich_text", "text"):
        return collapse(value)
    if kind == "list":
        return collapse("; ".join(value))
    if kind == "vocabulary":
        return "; ".join(term_labels(field_def["vocabulary"], value))
    if kind == "reference":
        return collapse("; ".join(reference_display(field_def["kind"], value)))
    if kind == "attachment":
        return f"{len(value)} anexo(s)"
    if kind == "date":
        return display_date(value)
    if kind == "number":
        return display_number(value, field_def.get("decimals"))
    if kind == "table":
        first = field_def["columns"][0]["key"]
        names = [cell_text(field_def["columns"][0], row.get(first)) for row in value]
        return collapse(f"{len(value)} linha(s): " + ", ".join(filter(None, names)))
    if kind == "applicability":
        applies = [row["codigo"] for row in value if row.get("aplica") == "sim"]
        not_applies = [row["codigo"] for row in value if row.get("aplica") == "nao"]
        parts = []
        if applies:
            parts.append("Aplica: " + ", ".join(term_labels(field_def["vocabulary"], applies)))
        if not_applies:
            parts.append(
                "Não se aplica: " + ", ".join(term_labels(field_def["vocabulary"], not_applies))
            )
        return collapse("; ".join(parts))
    return ""


def cell_text(column: dict, value) -> str:
    if value in (None, ""):
        return ""
    if column["type"] == "number":
        return display_number(value, column.get("decimals"))
    if column["type"] == "date":
        return display_date(value)
    if column["type"] == "reference":
        return (
            reference_display(column["kind"], value.get("id"))[0]
            if isinstance(value, dict)
            else str(value)
        )
    if column["type"] == "vocabulary":
        return term_labels(column["vocabulary"], value)[0]
    return str(value)


def references(field_def: dict, value) -> list[tuple[str, int]]:
    """Versões de cadastros referenciadas (bloqueadas na aprovação)."""
    kind = field_def["type"]
    found = []
    if kind == "reference" and value:
        ids = value if isinstance(value, list) else [value]
        found.extend((field_def["kind"], pk) for pk in ids)
    if kind == "table":
        for column in field_def["columns"]:
            if column["type"] == "reference":
                for row in value or []:
                    cell = row.get(column["key"])
                    if isinstance(cell, dict) and cell.get("id"):
                        found.append((column["kind"], cell["id"]))
    return found


def attachments(field_def: dict, value) -> list[int]:
    return list(value or []) if field_def["type"] == "attachment" else []


def has_table(field_def: dict, value) -> bool:
    kind = field_def["type"]
    if kind == "table":
        return bool(value)
    if kind == "applicability":
        return not is_empty(field_def, value)
    if kind == "derived_table":
        return bool((value or {}).get("rows"))
    return False


def column_total(field_def: dict, value, column_key: str) -> str:
    column = next(c for c in field_def["columns"] if c["key"] == column_key)
    total = sum(
        (
            Decimal(str(row[column_key]))
            for row in value or []
            if row.get(column_key) not in (None, "")
        ),
        Decimal(0),
    )
    return display_number(number_text(total), column.get("decimals"))
