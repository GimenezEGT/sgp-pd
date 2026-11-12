"""Conteúdo de cada fonte do dossiê, só de versões aprovadas (research R2 da feature 011).

Cada fonte devolve um `Part`: situação (completo, faltando, não aplicável), origem, blocos no
formato do conteúdo congelado da 006, anexos e as versões de origem usadas.
"""

from dataclasses import dataclass, field

from sgp.documents.content import NOT_FILLED, blocks_for_study, frozen
from sgp.signatures.models import ApprovedVersion
from sgp.subdocuments.models import Subdocument
from sgp.vocab.models import get_term

COMPLETE, MISSING, NOT_APPLICABLE = "complete", "missing", "na"
STATUS_LABELS = {COMPLETE: "Completo", MISSING: "Faltando", NOT_APPLICABLE: "Não aplicável"}


@dataclass
class Part:
    status: str
    origin: str
    blocks: list = field(default_factory=list)
    justification: str = ""
    reason: str = ""
    annexes: list = field(default_factory=list)
    used: list = field(default_factory=list)


def _rich(text: str) -> dict:
    items = []
    for block in (text or "").replace("\r\n", "\n").split("\n\n"):
        lines = [line for line in block.split("\n") if line.strip()]
        if lines and all(line.lstrip().startswith("- ") for line in lines):
            items.append({"ul": [line.lstrip()[2:] for line in lines]})
        elif lines:
            items.append({"p": "\n".join(lines)})
    return {"kind": "rich", "label": "", "items": items}


def _empty(block: dict) -> bool:
    kind = block.get("kind")
    if kind == "values":
        return not [line for line in block.get("lines", []) if line and line != NOT_FILLED]
    if kind == "table":
        return not block.get("rows")
    if kind == "files":
        return not block.get("files")
    if kind == "rich":
        return not block.get("items")
    return kind == "empty"


def _type_label(code: str) -> str:
    return get_term("tipo-subdocumento", code).label


def approved_versions(project, code: str) -> list[tuple]:
    """(subdocumento, aprovação vigente) de cada subdocumento aprovado do tipo, em sequência."""
    out = []
    for sub in Subdocument.objects.filter(project=project, subdocument_type__code=code).order_by(
        "sequence", "pk"
    ):
        approval = (
            ApprovedVersion.objects.filter(kind="subdocument", object_id=sub.pk)
            .order_by("-version")
            .first()
        )
        if approval is not None:
            out.append((sub, approval))
    return out


def _template(sub, approval):
    from sgp.formtemplates.models import FormTemplate

    template_id = ((approval.content or {}).get("modelo") or {}).get("id")
    return FormTemplate.objects.filter(pk=template_id).first() or sub.template


def _topic(template, key: str) -> dict | None:
    return next((topic for topic in template.topics if topic["key"] == key), None)


def subdocument(project, source: dict) -> Part:
    code, key = source["subdocumento"], source["topico"]
    versions = approved_versions(project, code)
    if not versions:
        return Part(MISSING, _type_label(code), reason=f"{_type_label(code)} sem versão aprovada.")
    blocks, used, origins = [], [], []
    for sub, approval in versions:
        rendering = frozen("subdocument", sub.pk, approval.version)
        template = _template(sub, approval)
        topic = _topic(template, key)
        origin = f"{_type_label(code)} – versão {approval.version:02d}"
        if topic is None:
            return Part(MISSING, origin, reason=f"Tópico '{key}' não existe no modelo.")
        label = topic.get("body_label") or topic["label"]
        origins.append(f"{origin} › {label}")
        if rendering is None:
            return Part(
                MISSING,
                origins[-1],
                reason="Versão aprovada sem conteúdo congelado (aprovada antes da geração de documentos).",
            )
        section = next((s for s in rendering.content["sections"] if s["label"] == label), None)
        if section is None:
            return Part(MISSING, origins[-1], reason="Tópico ausente no conteúdo aprovado.")
        used.append(
            {
                "tipo": "subdocumento",
                "id": sub.pk,
                "versao": approval.version,
                "resumo": rendering.content_hash,
            }
        )
        if section.get("not_applicable"):
            justification = (section.get("justification") or "").strip()
            if not justification:
                return Part(
                    MISSING, origins[-1], reason="Não aplicável sem justificativa.", used=used
                )
            return Part(NOT_APPLICABLE, origins[-1], justification=justification, used=used)
        wanted = None
        if source.get("campos"):
            labels = {f["key"]: f["label"] for f in topic.get("fields", [])}
            wanted = {labels.get(name, name) for name in source["campos"]}
        chosen = [
            block
            for block in section.get("blocks", [])
            if (wanted is None or block.get("label") in wanted) and not _empty(block)
        ]
        blocks += chosen
    if not blocks:
        return Part(MISSING, "; ".join(origins), reason="Tópico sem dados preenchidos.", used=used)
    return Part(COMPLETE, "; ".join(origins), blocks=blocks, used=used)


def _attachment_ids(values: dict, topic: dict) -> list[int]:
    ids = []
    for field_def in topic.get("fields", []):
        if field_def.get("type") != "attachment":
            continue
        value = values.get(field_def["key"]) or []
        for item in value if isinstance(value, list) else [value]:
            if isinstance(item, dict):
                item = item.get("id")
            if str(item).isdigit():
                ids.append(int(item))
    return ids


def attachments(project, source: dict) -> Part:
    from sgp.files.models import StoredFile

    code, key = source["subdocumento"], source["topico"]
    versions = approved_versions(project, code)
    if not versions:
        return Part(MISSING, _type_label(code), reason=f"{_type_label(code)} sem versão aprovada.")
    files, used, origins = [], [], []
    for sub, approval in versions:
        template = _template(sub, approval)
        topic = _topic(template, key)
        if topic is None:
            return Part(MISSING, _type_label(code), reason=f"Tópico '{key}' não existe no modelo.")
        origin = f"{_type_label(code)} – versão {approval.version:02d} › {topic['label']}"
        origins.append(origin)
        data = ((approval.content or {}).get("topicos") or {}).get(key) or {}
        if data.get("na"):
            justification = (data.get("justification") or "").strip()
            if justification:
                return Part(NOT_APPLICABLE, origin, justification=justification)
            return Part(MISSING, origin, reason="Não aplicável sem justificativa.")
        stored = StoredFile.objects.filter(pk__in=_attachment_ids(data.get("values") or {}, topic))
        if source.get("imagens"):
            stored = stored.filter(content_type__startswith="image/")
        files += list(stored.order_by("pk"))
        used.append({"tipo": "anexos", "id": sub.pk, "versao": approval.version})
    if not files:
        return Part(MISSING, "; ".join(origins), reason="Nenhum anexo no tópico.", used=used)
    return Part(COMPLETE, "; ".join(origins), annexes=files, used=used)


def studies(project, source: dict) -> Part:
    from sgp.studies.models import Study, StudyStatus

    codes = source["tipos"]
    latest = {}
    for study in (
        Study.objects.filter(project=project, study_type__code__in=codes)
        .select_related("study_type")
        .order_by("lineage", "-version")
    ):
        latest.setdefault(study.lineage, study)
    approved = [s for s in latest.values() if s.status == StudyStatus.LOCKED]
    labels = ", ".join(get_term("tipo-estudo", code).label for code in codes)
    origin = f"Estudos: {labels}"
    if not approved:
        return Part(
            MISSING, origin, reason="Sem estudo aprovado (bloqueado pela aprovação do documento)."
        )
    approved.sort(key=lambda s: (s.study_type.code, s.title))
    used = [{"tipo": "estudo", "id": s.pk, "versao": s.version} for s in approved]
    if all(s.not_applicable for s in approved):
        justification = "; ".join(s.justification for s in approved if s.justification)
        if not justification:
            return Part(MISSING, origin, reason="Não aplicável sem justificativa.", used=used)
        return Part(NOT_APPLICABLE, origin, justification=justification, used=used)
    blocks = []
    for study in approved:
        blocks += blocks_for_study(study)
    return Part(COMPLETE, origin, blocks=blocks, used=used)


def _reference_ids(project, kind: str, codes=None) -> list[int]:
    ids = []
    filters = {"project": project}
    if codes:
        filters["subdocument_type__code__in"] = codes
    for sub in Subdocument.objects.filter(**filters).order_by("pk"):
        approval = (
            ApprovedVersion.objects.filter(kind="subdocument", object_id=sub.pk)
            .order_by("-version")
            .first()
        )
        if approval is None:
            continue
        template = _template(sub, approval)
        topics = (approval.content or {}).get("topicos") or {}
        for topic in template.topics:
            values = (topics.get(topic["key"]) or {}).get("values") or {}
            for field_def in topic.get("fields", []):
                if field_def.get("type") == "reference" and field_def.get("kind") == kind:
                    value = values.get(field_def["key"]) or []
                    for item in value if isinstance(value, list) else [value]:
                        if isinstance(item, dict):
                            item = item.get("id")
                        if str(item).isdigit() and int(item) not in ids:
                            ids.append(int(item))
    return ids


def standards(project, source: dict) -> Part:
    from sgp.catalog.models import Standard

    ids = _reference_ids(project, "normas", ["entrada"])
    records = list(Standard.objects.filter(pk__in=ids).order_by("identifier"))
    if not records:
        return Part(
            MISSING,
            "Entrada de Projeto › Requisitos regulatórios",
            reason="Nenhuma norma citada na Entrada aprovada.",
        )
    lines = [f"{r.identifier} – {r.title}" for r in records]
    block = {"kind": "values", "label": "", "lines": lines}
    used = [{"tipo": "norma", "id": r.pk, "versao": r.version} for r in records]
    return Part(COMPLETE, "Entrada de Projeto › Requisitos regulatórios", blocks=[block], used=used)


def references(project, source: dict) -> Part:
    from sgp.catalog.models import BibliographicReference

    ids = _reference_ids(project, "referencias")
    records = list(BibliographicReference.objects.filter(pk__in=ids))
    records.sort(key=lambda r: ids.index(r.pk))
    if not records:
        return Part(
            MISSING, "Subdocumentos aprovados", reason="Nenhuma referência bibliográfica citada."
        )
    lines = [
        f"{number}. {' '.join(r.citation.split())}" for number, r in enumerate(records, start=1)
    ]
    used = [{"tipo": "referencia", "id": r.pk, "versao": r.version} for r in records]
    return Part(
        COMPLETE,
        "Subdocumentos aprovados (referências citadas)",
        blocks=[{"kind": "values", "label": "", "lines": lines}],
        used=used,
    )


def standard_text(project, source: dict) -> Part:
    from .models import StandardText, TextStatus

    text = StandardText.objects.filter(key=source["chave"], status=TextStatus.APPROVED).first()
    origin = f"Texto padrão '{source['chave']}'"
    if text is None:
        return Part(MISSING, origin, reason="Texto padrão sem versão aprovada.")
    return Part(
        COMPLETE,
        f"{origin} – versão {text.version}",
        blocks=[_rich(text.text)],
        used=[{"tipo": "texto_padrao", "id": text.pk, "chave": text.key, "versao": text.version}],
    )


def supplement(project, source: dict, item_key: str) -> Part:
    from .models import DossierSupplement

    record = DossierSupplement.objects.filter(project=project, item_key=item_key).first()
    origin = "Complemento do dossiê (Assuntos Regulatórios)"
    if record is None:
        return Part(MISSING, origin, reason="Complemento não preenchido.")
    used = [{"tipo": "complemento", "id": record.pk, "atualizado": record.updated_at.isoformat()}]
    if record.not_applicable:
        if not record.justification.strip():
            return Part(MISSING, origin, reason="Não aplicável sem justificativa.", used=used)
        return Part(NOT_APPLICABLE, origin, justification=record.justification.strip(), used=used)
    if not record.text.strip():
        return Part(MISSING, origin, reason="Complemento vazio.", used=used)
    return Part(COMPLETE, origin, blocks=[_rich(record.text)], used=used)


def evaluate(project, source: dict, item_key: str) -> Part:
    kind = source["tipo"]
    if kind == "subdocumento":
        return subdocument(project, source)
    if kind == "anexos":
        return attachments(project, source)
    if kind == "estudos":
        return studies(project, source)
    if kind == "normas":
        return standards(project, source)
    if kind == "referencias":
        return references(project, source)
    if kind == "texto_padrao":
        return standard_text(project, source)
    return supplement(project, source, item_key)
