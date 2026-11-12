"""O que falta para o documento completo ser oficial (FR-012; research R8)."""

from sgp.documents.content import frozen
from sgp.signatures.models import ApprovedVersion
from sgp.subdocuments.flow import FLOW
from sgp.subdocuments.models import CHANGE, Subdocument
from sgp.vocab.models import get_term

APPROVED_DISPOSITION = "aprovado"
CHECKLIST_SOURCE = "entry_topics"
FINAL_CHECK = "verificacao-final"


def latest_approval(kind: str, object_id: int) -> ApprovedVersion | None:
    return (
        ApprovedVersion.objects.filter(kind=kind, object_id=object_id).order_by("-version").first()
    )


def _label(code: str) -> str:
    return get_term("tipo-subdocumento", code).label


def _project_parts(project) -> list[str]:
    items = []
    for kind, label, obj in (
        ("charter", "Termo de Abertura do Projeto", getattr(project, "charter", None)),
        ("business_plan", "Plano de Negócios", getattr(project, "business_plan", None)),
    ):
        approval = latest_approval(kind, obj.pk) if obj else None
        if approval is None:
            items.append(f"{label}: sem versão aprovada.")
        elif frozen(kind, obj.pk, approval.version) is None:
            items.append(
                f"{label}: versão {approval.version:02d} aprovada sem conteúdo congelado para "
                "geração (aprovada antes da geração de documentos); aprove nova versão."
            )
    return items


def _final_check_items(sub, approval) -> list[str]:
    from sgp.formtemplates.fieldtypes import term_labels
    from sgp.formtemplates.models import FormTemplate

    content = approval.content or {}
    template_id = (content.get("modelo") or {}).get("id")
    template = FormTemplate.objects.filter(pk=template_id).first() or sub.template
    topics = content.get("topicos") or {}
    items = []
    for topic in template.topics:
        for field in topic.get("fields", []):
            if field.get("type") != "derived_table" or field.get("source") != CHECKLIST_SOURCE:
                continue
            justify = field.get("justify_unless") or {}
            column = justify.get("column")
            reason_key = justify.get("justification")
            vocabulary = next(
                (c.get("vocabulary") for c in field.get("columns", []) if c["key"] == column), ""
            )
            data = ((topics.get(topic["key"]) or {}).get("values") or {}).get(field["key"]) or {}
            for index, row in enumerate(data.get("rows", []), start=1):
                values = row.get("values", {})
                disposition = values.get(column, "")
                if disposition == (justify.get("value") or APPROVED_DISPOSITION):
                    continue
                shown = (
                    term_labels(vocabulary, disposition)[0]
                    if vocabulary and disposition
                    else "sem disposição"
                )
                reason = values.get(reason_key, "") if reason_key else ""
                items.append(
                    f"Verificação Final, item {index} – {row.get('label', '')}: disposição "
                    f"{shown}" + (f" (justificativa: {reason})" if reason else "") + "."
                )
    return items


def pending_items(project) -> list[str]:
    """Pendências na ordem do documento; lista vazia significa documento oficial."""
    items = _project_parts(project)
    for code in (*FLOW, CHANGE):
        subs = list(
            Subdocument.objects.filter(project=project, subdocument_type__code=code)
            .select_related("subdocument_type", "template")
            .order_by("sequence", "pk")
        )
        if not subs and code != CHANGE:
            items.append(f"{_label(code)}: não criado.")
        for sub in subs:
            approval = latest_approval("subdocument", sub.pk)
            if approval is None:
                items.append(f"{sub}: sem versão aprovada ({sub.get_status_display().lower()}).")
                continue
            if frozen("subdocument", sub.pk, approval.version) is None:
                items.append(
                    f"{sub}: versão {approval.version:02d} aprovada sem conteúdo congelado para "
                    "geração (aprovada antes da geração de documentos); aprove nova versão."
                )
            if code == FINAL_CHECK:
                items.extend(_final_check_items(sub, approval))
    return items
