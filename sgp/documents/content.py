"""Conteúdo de renderização (contrato conteudo-renderizacao.md da feature 006).

Monta, a partir do documento, tudo o que o PDF e o DOCX desenham, já resolvido em texto: rótulos
de lista, valores de cadastro na versão referenciada, números com vírgula decimal e datas
dd/mm/aaaa. Nada é digitado no gerador (FR-001). Na aprovação, o conteúdo é congelado com as
assinaturas (FR-017).
"""

import math

from django.db import transaction
from django.utils import timezone

from sgp.audit.services import record_event
from sgp.core.formatting import format_decimal_br
from sgp.files.models import StoredFile
from sgp.formtemplates import fieldtypes
from sgp.signatures.canonical import content_hash, normalized
from sgp.signatures.models import DocumentKind, Meaning, Signature

from .layouts import layout_for
from .models import FrozenRendering

FORMAT = 1
NOT_FILLED = "(não preenchido)"
CHECKLIST_SOURCE = "entry_topics"
SECTORS_VOCABULARY = "setor-transferencia"
OPTIONAL_FORM = "formulario_opcional"
DASH = chr(0x2013)
TITLES = {
    DocumentKind.CHARTER: "Termo de Abertura de Projeto",
    DocumentKind.BUSINESS_PLAN: "Plano de Negócios",
}
MEANING_LABELS = dict(Meaning.choices)


# ------------------------------------------------------------------ utilidades


def two_digits(value) -> str:
    return f"{int(value):02d}" if value not in (None, "") else ""


def date_br(value) -> str:
    return value.strftime("%d/%m/%Y") if value else ""


def datetime_br(value) -> str:
    return timezone.localtime(value).strftime("%d/%m/%Y %H:%M") if value else ""


def money(value) -> str:
    return f"R$ {format_decimal_br(value, 2)}" if value not in (None, "") else ""


def rich_items(text: str) -> list[dict]:
    """Parágrafos e listas simples ("- "), como no texto formatado da feature 004."""
    items = []
    for block in (text or "").replace("\r\n", "\n").split("\n\n"):
        lines = [line for line in block.split("\n") if line.strip()]
        if not lines:
            continue
        if all(line.lstrip().startswith("- ") for line in lines):
            items.append({"ul": [line.lstrip()[2:] for line in lines]})
        else:
            items.append({"p": "\n".join(lines)})
    return items


def _table(label: str, columns: list[str], rows: list[list[str]], totals=None) -> dict:
    return {
        "kind": "table",
        "number": "",
        "label": label,
        "columns": columns,
        "rows": rows,
        "totals": totals,
        "notes": [],
    }


def _values(label: str, lines: list[str]) -> dict:
    return {"kind": "values", "label": label, "lines": [line for line in lines if line != ""]}


def _number_tables(sections: list[dict]) -> None:
    """Tabelas numeradas em sequência no documento ("Tabela 01"), só as que têm linhas."""
    count = 0
    for section in sections:
        for block in section["blocks"]:
            if block["kind"] == "table" and block["rows"]:
                count += 1
                block["number"] = f"Tabela {count:02d}"


# ------------------------------------------------------------------ subdocumento


def _derived_table(field_def: dict, value) -> tuple[list[str], list[list[str]]]:
    from sgp.subdocuments.derived import FIXED_COLUMNS

    fixed = FIXED_COLUMNS[field_def["source"]]
    columns = [label for _, label in fixed] + [c["label"] for c in field_def.get("columns", [])]
    rows = []
    for row in (value or {}).get("rows", []):
        fixed_values = dict(row.get("fixed", {}))
        cells = [row.get("label", "")] + [str(fixed_values.get(key, "")) for key, _ in fixed[1:]]
        for column in field_def.get("columns", []):
            raw = row.get("values", {}).get(column["key"], "")
            cells.append(
                fieldtypes.term_labels(column["vocabulary"], raw)[0]
                if column["type"] == "vocabulary" and raw
                else str(raw or "")
            )
        rows.append(cells)
    return columns, rows


def _applicability(field_def: dict, value) -> list[list[str]]:
    current = {row["codigo"]: row for row in value or []}
    rows = []
    for term in fieldtypes.vocabulary_terms(field_def["vocabulary"]).order_by("position"):
        row = current.get(term.code)
        if not row:
            continue
        applies = {"sim": "Aplica", "nao": "Não se aplica"}.get(row.get("aplica", ""), "")
        rows.append([term.label, applies, row.get("criterio", ""), row.get("justificativa", "")])
    return rows


def _field_block(field_def: dict, value, sub, entry_labels: dict) -> dict | None:
    kind = field_def["type"]
    label = fieldtypes.label_of(field_def)
    if kind == "note":
        return {"kind": "note", "text": field_def.get("text", "")}
    if kind == "lots_production":
        from sgp.catalog.kinds import get_kind

        topic_key, field_key = field_def["source_field"].split(".", 1)
        ids = sub.topic_data(topic_key)["values"].get(field_key) or []
        ids = ids if isinstance(ids, list) else [ids]
        lots = (
            get_kind("lotes")
            .model.objects.filter(pk__in=ids)
            .select_related("production_responsible")
        )
        lines = [
            f"{lot.display} {DASH} responsável: {lot.production_responsible.get_full_name()} "
            f"{DASH} local: {lot.manufacturing_site}"
            for lot in lots
        ]
        return _values(label, lines) if lines else None
    if fieldtypes.is_empty(field_def, value):
        if field_def.get("required"):
            return {"kind": "empty", "label": label, "text": NOT_FILLED}
        return None
    if kind == "rich_text":
        return {"kind": "rich", "label": label, "items": rich_items(value)}
    if kind == "text":
        return _values(label, [str(value)])
    if kind == "list":
        return _values(label, list(value))
    if kind == "vocabulary":
        return _values(label, fieldtypes.term_labels(field_def["vocabulary"], value))
    if kind == "reference":
        return _values(label, fieldtypes.reference_display(field_def["kind"], value))
    if kind == "attachment":
        files = StoredFile.objects.filter(pk__in=value).order_by("pk")
        return {
            "kind": "files",
            "label": label,
            "files": [{"name": item.original_name, "sha256": item.sha256} for item in files],
        }
    if kind == "date":
        return _values(label, [fieldtypes.display_date(value)])
    if kind == "number":
        return _values(label, [fieldtypes.display_number(value, field_def.get("decimals"))])
    if kind == "table":
        columns = field_def["columns"]
        rows = [[fieldtypes.cell_text(c, row.get(c["key"])) for c in columns] for row in value]
        totals = [
            fieldtypes.column_total(field_def, value, c["key"]) if c.get("sum") else ""
            for c in columns
        ]
        return _table(label, [c["label"] for c in columns], rows, totals if any(totals) else None)
    if kind == "applicability":
        columns = ["Requisito", "Aplica", "Critério de aceitação", "Justificativa"]
        return _table(label, columns, _applicability(field_def, value))
    if kind == "derived_table":
        columns, rows = _derived_table(field_def, value)
        return _table(label, columns, rows)
    if kind == "entry_topics":
        return _values(label, [entry_labels.get(key, key) for key in value])
    if kind == "subdocuments":
        from sgp.subdocuments.models import Subdocument

        others = Subdocument.objects.filter(pk__in=value).select_related("subdocument_type")
        return _values(label, [str(other) for other in others])
    return None


def _checklist(topic: dict, data: dict) -> dict | None:
    """Variante `checklist`: a tabela CHECK LIST com os dados vai para a capa (FR-005)."""
    field_def = next(
        (
            f
            for f in topic.get("fields", [])
            if f["type"] == "derived_table" and f.get("source") == CHECKLIST_SOURCE
        ),
        None,
    )
    if field_def is None:
        return None
    from sgp.subdocuments.derived import FIXED_COLUMNS

    justify = field_def.get("justify_unless") or {}
    merged = justify.get("justification")
    disposition = justify.get("column")
    columns = [label for _, label in FIXED_COLUMNS[CHECKLIST_SOURCE]]
    template_columns = [c for c in field_def.get("columns", []) if c["key"] != merged]
    columns += [c["label"] for c in template_columns]
    rows = []
    value = data["values"].get(field_def["key"]) or {}
    for index, row in enumerate(value.get("rows", []), start=1):
        values = row.get("values", {})
        cells = [f"{index} - {row.get('label', '')}", str(row.get("fixed", {}).get("previsto", ""))]
        for column in template_columns:
            raw = values.get(column["key"], "")
            text = (
                fieldtypes.term_labels(column["vocabulary"], raw)[0]
                if column["type"] == "vocabulary" and raw
                else str(raw or "")
            )
            if column["key"] == disposition and merged and values.get(merged):
                text = f"{text}\nJustificativa: {values[merged]}".strip()
            cells.append(text)
        rows.append(cells)
    return {"title": topic["label"], "columns": [c.upper() for c in columns], "rows": rows}


def _sectors(sub) -> dict | None:
    """Variante `sectors`: todos os setores em duas colunas, marcando os escolhidos (FR-005)."""
    for topic in sub.template.topics:
        for field_def in topic.get("fields", []):
            if (
                field_def["type"] == "vocabulary"
                and field_def.get("vocabulary") == SECTORS_VOCABULARY
            ):
                chosen = sub.topic_data(topic["key"])["values"].get(field_def["key"]) or []
                chosen = chosen if isinstance(chosen, list) else [chosen]
                terms = [
                    term
                    for term in fieldtypes.vocabulary_terms(SECTORS_VOCABULARY).order_by(
                        "position", "label"
                    )
                    if term.is_active or term.code in chosen
                ]
                items = [{"label": t.label.upper(), "checked": t.code in chosen} for t in terms]
                half = math.ceil(len(items) / 2)
                return {"columns": [items[:half], items[half:]]}
    return None


def _optional_form(sub, topic: dict, data: dict) -> dict | None:
    values = data["values"]
    fields = [f for f in topic.get("fields", []) if f["type"] != "note"]
    if not any(not fieldtypes.is_empty(f, values.get(f["key"])) for f in fields):
        return None
    lines = [f"Nome do Projeto: {sub.project.title}", f"Versão: {sub.version_display}"]
    groups, note = [], ""
    for field_def in topic.get("fields", []):
        value = values.get(field_def["key"])
        if field_def["type"] == "note":
            note = field_def.get("text", "")
        elif field_def["type"] == "vocabulary":
            chosen = value if isinstance(value, list) else [value] if value else []
            options = [
                {"label": term.label, "checked": term.code in chosen}
                for term in fieldtypes.vocabulary_terms(field_def["vocabulary"]).order_by(
                    "position", "label"
                )
                if term.is_active or term.code in chosen
            ]
            groups.append({"label": fieldtypes.label_of(field_def), "options": options})
        elif field_def["type"] == "date":
            lines.append(f"{fieldtypes.label_of(field_def)}: {fieldtypes.display_date(value)}")
        else:
            lines.append(f"{fieldtypes.label_of(field_def)}: {value or ''}")
    return {"title": topic["label"], "lines": lines, "groups": groups, "note": note}


def subdocument_content(sub, layout_definition: dict) -> dict:
    from sgp.subdocuments import numbering
    from sgp.subdocuments.services import entry_topics

    template = sub.template
    type_code = sub.subdocument_type.code
    variant = layout_definition["cover"].get("variant_by_type", {}).get(type_code, "topics")
    entry_labels = entry_topics(sub.project)[1]
    cover_topics, sections = [], []
    checklist = optional_form = None
    for number, topic in numbering.visible_topics(sub):
        data = sub.topic_data(topic["key"])
        if number is None:
            if topic["key"] == OPTIONAL_FORM:
                optional_form = _optional_form(sub, topic, data)
            continue
        cover_topics.append([number, topic["label"]])
        if variant == "checklist" and checklist is None:
            checklist = _checklist(topic, data)
            if checklist is not None:
                continue
        blocks = []
        if not data["na"]:
            for field_def in topic.get("fields", []):
                block = _field_block(
                    field_def, data["values"].get(field_def["key"]), sub, entry_labels
                )
                if block is not None:
                    blocks.append(block)
        sections.append(
            {
                "number": number,
                "label": topic.get("body_label") or topic["label"],
                "not_applicable": data["na"],
                "justification": data["justification"],
                "blocks": blocks,
            }
        )
    _number_tables(sections)
    is_change = bool(template.cover.get("change_versions"))
    return {
        "format": FORMAT,
        "kind": DocumentKind.SUBDOCUMENT.value,
        "type": type_code,
        "title": template.cover.get("title") or sub.subdocument_type.label,
        "product": sub.project.product_name.upper(),
        "project_code": sub.project.code or "",
        "version": sub.version_display,
        "changed_version": two_digits(sub.changed_version) if is_change else None,
        "new_version": two_digits(sub.new_version) if is_change else None,
        "form_footer": template.footer,
        "form_template": template.pk,
        "cover": {
            "columns": template.cover.get("columns", 1),
            "topics": [] if checklist else cover_topics,
            "approver_label": template.cover.get("approver_label") or "Gestor de P&D:",
            "author_label": "Analista Responsável (Nome/Função):",
            "checklist": checklist,
            "sectors": _sectors(sub) if variant == "sectors" else None,
        },
        "sections": sections,
        "optional_form": optional_form,
        "signatures": [],
        "approved_on": "",
    }


# --------------------------------------------------------- TAP e Plano de Negócios


def _field_label(model, field: str) -> str:
    label = str(model._meta.get_field(field).verbose_name)
    return label[:1].upper() + label[1:]


def _project_base(kind: str, obj, project) -> dict:
    return {
        "format": FORMAT,
        "kind": kind,
        "type": kind,
        "title": TITLES[kind],
        "product": project.product_name.upper(),
        "project_code": project.code or "",
        "version": two_digits(obj.doc_version),
        "changed_version": None,
        "new_version": None,
        "form_footer": "",
        "form_template": None,
        "cover": {
            "columns": 1,
            "topics": [],
            "approver_label": "Aprovado (Nome/Função):",
            "author_label": "Elaborado (Nome/Função):",
            "checklist": None,
            "sectors": None,
        },
        "optional_form": None,
        "signatures": [],
        "approved_on": "",
    }


def _numbered(sections: list[dict]) -> list[dict]:
    for number, section in enumerate(sections, start=1):
        section["number"] = number
    _number_tables(sections)
    return sections


def _section(label: str, blocks: list[dict]) -> dict:
    return {
        "number": 0,
        "label": label,
        "not_applicable": False,
        "justification": "",
        "blocks": [block for block in blocks if block is not None],
    }


def charter_content(charter) -> dict:
    from sgp.projects.models import Project, ProjectCharter

    project = charter.project
    product_lines = [
        f"{_field_label(Project, field)}: {value}"
        for field, value in (
            ("product_name", project.product_name),
            ("product_family", project.product_family),
            ("technology", project.technology.label if project.technology_id else ""),
            ("regulatory_body", project.get_regulatory_body_display()),
            ("risk_class", project.get_risk_class_display() if project.risk_class else ""),
            ("classification_rule", project.classification_rule),
        )
        if value
    ]
    sections = [_section("Produto", [_values("", product_lines)])]
    for field in ("justification", "objective"):
        text = getattr(charter, field)
        sections.append(
            _section(
                _field_label(ProjectCharter, field),
                [{"kind": "rich", "label": "", "items": rich_items(text)}] if text else [],
            )
        )
    for field in ("scope_included", "scope_excluded", "deliverables", "assumptions", "constraints"):
        sections.append(
            _section(_field_label(ProjectCharter, field), [_values("", getattr(charter, field))])
        )
    sections.append(
        _section(
            _field_label(ProjectCharter, "risks"),
            [
                _table(
                    _field_label(ProjectCharter, "risks"),
                    ["Risco", "Impacto", "Resposta"],
                    [
                        [r.get("risco", ""), r.get("impacto", ""), r.get("resposta", "")]
                        for r in charter.risks
                    ],
                )
            ],
        )
    )
    sections.append(
        _section(
            _field_label(ProjectCharter, "stakeholders"),
            [
                _table(
                    _field_label(ProjectCharter, "stakeholders"),
                    ["Nome/área", "Interesse"],
                    [
                        [s.get("nome_area", ""), s.get("interesse", "")]
                        for s in charter.stakeholders
                    ],
                )
            ],
        )
    )
    members = project.members.select_related("user").order_by("start_date", "pk")
    sections.append(
        _section(
            "Equipe",
            [
                _table(
                    "Equipe",
                    ["Pessoa", "Papel no projeto", "Início", "Fim"],
                    [
                        [
                            m.user.get_full_name() or m.user.username,
                            m.role,
                            date_br(m.start_date),
                            date_br(m.end_date),
                        ]
                        for m in members
                    ],
                )
            ],
        )
    )
    milestones = project.milestones.select_related("subdocument_type").order_by(
        "planned_date", "pk"
    )
    sections.append(
        _section(
            "Marcos planejados",
            [
                _table(
                    "Marcos planejados",
                    ["Subdocumento", "Descrição", "Data planejada", "Data realizada"],
                    [
                        [
                            m.subdocument_type.label,
                            m.description,
                            date_br(m.planned_date),
                            date_br(m.actual_date),
                        ]
                        for m in milestones
                        if m.canceled_at is None
                    ],
                )
            ],
        )
    )
    content = _project_base(DocumentKind.CHARTER.value, charter, project)
    content["sections"] = _numbered(sections)
    return content


def plan_content(plan) -> dict:
    from django.db import models as dj

    from sgp.projects.models import BusinessPlan
    from sgp.projects.services import PLAN_FIELDS

    sections = []
    for field in PLAN_FIELDS:
        model_field = BusinessPlan._meta.get_field(field)
        value = getattr(plan, field)
        label = _field_label(BusinessPlan, field)
        if isinstance(model_field, dj.DecimalField):
            blocks = [_values("", [money(value)])]
        elif isinstance(model_field, dj.DateField):
            blocks = [_values("", [date_br(value)])]
        elif isinstance(model_field, dj.JSONField):
            blocks = [_values("", list(value or []))]
        elif isinstance(model_field, dj.TextField):
            blocks = [{"kind": "rich", "label": "", "items": rich_items(value)}] if value else []
        else:
            blocks = [_values("", [str(value) if value not in (None, "") else ""])]
        sections.append(_section(label, blocks))
    forecasts = {f.year_index: f.amount for f in plan.forecasts.order_by("year_index")}
    rows = [[f"Ano {year}", money(forecasts.get(year))] for year in range(1, 6)]
    sections.append(
        _section(
            "Retorno esperado (5 anos)",
            [
                _table(
                    "Retorno esperado (5 anos)",
                    ["Ano", "Valor"],
                    rows,
                    ["Total", money(plan.forecast_total)],
                )
            ],
        )
    )
    content = _project_base(DocumentKind.BUSINESS_PLAN.value, plan, plan.project)
    content["sections"] = _numbered(sections)
    return content


# ------------------------------------------------------------------ montagem


def build(kind: str, obj, layout) -> dict:
    """Conteúdo do momento (rascunho ou versão aprovada ainda sem congelamento)."""
    if kind == DocumentKind.SUBDOCUMENT:
        return subdocument_content(obj, layout.definition)
    if kind == DocumentKind.CHARTER:
        return charter_content(obj)
    return plan_content(obj)


def signature_lines(kind: str, object_id: int, version: int, digest: str) -> list[dict]:
    """Assinaturas da versão sobre o conteúdo aprovado, em ordem de data e hora."""
    signatures = (
        Signature.objects.filter(
            kind=kind, object_id=object_id, version=version, content_hash=digest
        )
        .select_related("delegation__delegator")
        .order_by("signed_at", "pk")
    )
    lines = []
    for signature in signatures:
        delegation = ""
        if signature.delegation_id:
            delegator = signature.delegation.delegator
            delegation = f"em delegação de {delegator.get_full_name() or delegator.username}"
        lines.append(
            {
                "meaning": MEANING_LABELS[signature.meaning],
                "meaning_code": signature.meaning,
                "name": signature.signer_name,
                "title": signature.signer_title,
                "at": datetime_br(signature.signed_at),
                "delegation": delegation,
            }
        )
    return lines


def frozen(kind: str, object_id: int, version: int) -> FrozenRendering | None:
    return FrozenRendering.objects.filter(kind=kind, object_id=object_id, version=version).first()


def freeze(kind: str, obj, *, approved) -> FrozenRendering:
    """Congela o conteúdo exibido da versão aprovada (mesma transação da aprovação)."""
    from sgp.signatures.documents import get_adapter

    adapter = get_adapter(kind)
    version = adapter.version(obj)
    existing = frozen(kind, obj.pk, version)
    if existing:
        return existing
    layout = layout_for(kind, obj.pk, version)
    content = build(kind, obj, layout)
    content["signatures"] = signature_lines(kind, obj.pk, version, approved.content_hash)
    content["approved_on"] = date_br(timezone.localtime(approved.approved_at).date())
    content["approved_hash"] = approved.content_hash
    content = normalized(content)
    with transaction.atomic():
        rendering = FrozenRendering.objects.create(
            kind=kind,
            object_id=obj.pk,
            version=version,
            project=adapter.project(obj),
            layout=layout,
            content=content,
            content_hash=content_hash(content),
        )
        record_event(
            "documents.frozen",
            actor=approved.approved_by,
            object_type=f"documents.{kind}",
            object_id=obj.pk,
            object_repr=adapter.title(obj),
            project_id=adapter.project(obj).pk,
            new_value={
                "versao": two_digits(version),
                "modelo_layout": layout.version_display,
                "resumo": rendering.content_hash,
            },
        )
    return rendering
