"""Partes do documento completo na ordem do contrato estrutura-documento.md (research R6 a R10).

Tudo vem de registros já fechados: conteúdo congelado na aprovação (006), assinaturas (005),
entradas assinadas do caderno (008) e trilha de auditoria (001). Nada é remontado do rascunho.
"""

import base64
import copy
import re

from django.core.exceptions import FieldDoesNotExist
from django.db.models import Count
from django.utils import timezone

from sgp.audit.event_types import label_for
from sgp.audit.models import AuditEvent
from sgp.documents.content import date_br, datetime_br, frozen
from sgp.files.storage import read_verified
from sgp.notebook import richtext
from sgp.notebook.models import TEXT_FIELDS, TEXT_LABELS, EntryStatus, NotebookEntry
from sgp.projects.models import BusinessPlan
from sgp.projects.permissions import FINANCIAL_FIELDS
from sgp.signatures.canonical import content_hash
from sgp.signatures.models import ApprovedVersion, Meaning, Signature
from sgp.subdocuments.flow import FLOW
from sgp.subdocuments.models import CHANGE, Subdocument

from .models import NOTEBOOK_FULL

BEFORE_CHANGES = FLOW[: FLOW.index("verificacao-final")]
AFTER_CHANGES = FLOW[FLOW.index("verificacao-final") :]
FINANCIAL_NOTE = "Dado financeiro omitido (acesso restrito)."
RETURN_SECTION = "Retorno esperado (5 anos)"
DASH = chr(0x2013)
IMAGE_SRC = re.compile(r'src="/arquivos/(\d+)/"')
KEY_EVENTS = (
    "projects.submitted",
    "projects.returned",
    "projects.approved",
    "signatures.submitted",
    "signatures.signed",
    "signatures.returned",
    "signatures.approved",
    "signatures.new_version",
    "studies.new_version",
    "notebook.signed",
    "notebook.witnessed",
    "notebook.addendum_added",
    "fulldoc.generated",
)
MEANINGS = dict(Meaning.choices)


def financial_labels() -> set[str]:
    labels = {RETURN_SECTION}
    for field in FINANCIAL_FIELDS:
        try:
            name = getattr(BusinessPlan._meta.get_field(field), "verbose_name", None)
        except FieldDoesNotExist:
            continue
        if name:
            label = str(name)
            labels.add(label[:1].upper() + label[1:])
    return labels


def mask_financials(content: dict) -> dict:
    masked = copy.deepcopy(content)
    labels = financial_labels()
    for section in masked.get("sections", []):
        if section.get("label") in labels:
            section["blocks"] = [{"kind": "note", "text": FINANCIAL_NOTE}]
    return masked


def _approvals(kind: str, object_id: int) -> list[ApprovedVersion]:
    return list(ApprovedVersion.objects.filter(kind=kind, object_id=object_id).order_by("-version"))


def _document_part(kind, obj, approval, *, title, superseded=False, mask=False):
    rendering = frozen(kind, obj.pk, approval.version)
    if rendering is None:
        return None
    content = mask_financials(rendering.content) if mask else rendering.content
    label = f"{title} {DASH} versão {approval.version:02d}"
    return {
        "kind": "document",
        "doc_kind": kind,
        "object_id": obj.pk,
        "version": approval.version,
        "content": content,
        "content_hash": rendering.content_hash,
        "layout_id": rendering.layout_id,
        "superseded": superseded,
        "masked": mask,
        "approved_on": date_br(timezone.localtime(approval.approved_at).date()),
        "toc": label + (" (substituída)" if superseded else ""),
    }


def _document_parts(kind, obj, *, title, history, mask=False) -> list[dict]:
    approvals = _approvals(kind, obj.pk)
    chosen = approvals if history else approvals[:1]
    parts = []
    for index, approval in enumerate(chosen):
        part = _document_part(kind, obj, approval, title=title, superseded=index > 0, mask=mask)
        if part:
            parts.append(part)
    return parts


def subdocument_title(sub) -> str:
    label = sub.subdocument_type.label
    return f"{label} {sub.sequence}" if sub.subdocument_type.code == CHANGE else label


def _subdocuments(project, codes) -> list[Subdocument]:
    order = {code: position for position, code in enumerate(codes)}
    subs = Subdocument.objects.filter(
        project=project, subdocument_type__code__in=codes
    ).select_related("subdocument_type")
    return sorted(subs, key=lambda sub: (order[sub.subdocument_type.code], sub.sequence, sub.pk))


def _changes(project) -> list[Subdocument]:
    subs = []
    for sub in Subdocument.objects.filter(
        project=project, subdocument_type__code=CHANGE
    ).select_related("subdocument_type"):
        approvals = _approvals("subdocument", sub.pk)
        if approvals:
            subs.append((approvals[0].approved_at, sub.sequence, sub))
    return [sub for *_, sub in sorted(subs, key=lambda item: (item[0], item[1]))]


def documents_in_order(project) -> list[tuple[str, object, str]]:
    """(tipo, registro, título) de cada documento, na ordem do contrato."""
    items = []
    charter = getattr(project, "charter", None)
    plan = getattr(project, "business_plan", None)
    if charter is not None:
        items.append(("charter", charter, "Termo de Abertura do Projeto"))
    if plan is not None:
        items.append(("business_plan", plan, "Plano de Negócios"))
    for sub in _subdocuments(project, BEFORE_CHANGES):
        items.append(("subdocument", sub, subdocument_title(sub)))
    for sub in _changes(project):
        items.append(("subdocument", sub, subdocument_title(sub)))
    for sub in _subdocuments(project, AFTER_CHANGES):
        items.append(("subdocument", sub, subdocument_title(sub)))
    return items


# ------------------------------------------------------------------ partes de apoio


def version_rows(documents) -> list[dict]:
    rows = []
    for kind, obj, title in documents:
        approvals = list(reversed(_approvals(kind, obj.pk)))
        if not approvals:
            continue
        latest = approvals[-1].version
        for approval in approvals:
            signers = Signature.objects.filter(
                kind=kind, object_id=obj.pk, version=approval.version
            ).order_by("signed_at", "pk")
            rows.append(
                {
                    "document": title,
                    "version": f"{approval.version:02d}",
                    "approved_on": date_br(timezone.localtime(approval.approved_at).date()),
                    "signers": [
                        f"{s.signer_name} ({MEANINGS.get(s.meaning, s.meaning)}, "
                        f"{datetime_br(s.signed_at)})"
                        for s in signers
                    ],
                    "situation": "Vigente" if approval.version == latest else "Substituída",
                }
            )
    return rows


def audit_summary(project, until) -> dict:
    events = AuditEvent.objects.filter(project_id=project.pk, occurred_at__lte=until)
    first = events.order_by("seq").first()
    last = events.order_by("-seq").first()
    counts = events.values("event_type").annotate(total=Count("seq"))
    by_type = sorted(
        ((label_for(item["event_type"]), item["total"]) for item in counts),
        key=lambda pair: pair[0],
    )
    key_events = events.filter(event_type__in=KEY_EVENTS) | events.filter(
        event_type="documents.generated", new_value__oficial=True
    )
    rows = [
        {
            "at": datetime_br(event.occurred_at),
            "who": event.actor_username,
            "event": label_for(event.event_type),
            "record": event.object_repr,
        }
        for event in key_events.order_by("seq")
    ]
    return {
        "first": datetime_br(first.occurred_at) if first else "",
        "last": datetime_br(last.occurred_at) if last else "",
        "total": sum(total for _, total in by_type),
        "by_type": by_type,
        "key_events": rows,
    }


def _link_text(link) -> str:
    target = link.subdocument or link.lot or link.study
    return f"{link.get_target_type_display()} {target} ({link.get_kind_display().lower()})"


def _embed_images(html: str, images: dict) -> str:
    def replace(match):
        uri = images.get(int(match.group(1)))
        return f'src="{uri}"' if uri else 'src=""'

    return IMAGE_SRC.sub(replace, html)


def notebook(project, mode: str) -> list[dict]:
    entries = (
        NotebookEntry.objects.filter(
            project=project, status__in=[EntryStatus.SIGNED, EntryStatus.WITNESSED]
        )
        .select_related("author")
        .order_by("number")
    )
    items = []
    for entry in entries:
        signatures = entry.signatures.select_related("signer").order_by("signed_at", "pk")
        item = {
            "id": entry.pk,
            "number": entry.number,
            "title": entry.title,
            "date": datetime_br(entry.created_at),
            "author": entry.author.get_full_name() or entry.author.username,
            "status": entry.get_status_display(),
            "conclusion": richtext.plain_text(entry.conclusion),
            "links": [_link_text(link) for link in entry.links.filter(removed_at__isnull=True)],
            "signatures": [
                {
                    "role": s.get_role_display()
                    + (f" (adendo {s.addendum.number})" if s.addendum_id else ""),
                    "name": s.signer.get_full_name() or s.signer.username,
                    "at": datetime_br(s.signed_at),
                    "hash": s.content_hash,
                }
                for s in signatures
            ],
        }
        if mode == NOTEBOOK_FULL:
            attachments = entry.attachments.filter(removed_at__isnull=True).select_related("file")
            images = {}
            for attachment in attachments:
                if attachment.is_image:
                    data = read_verified(attachment.file)
                    encoded = base64.b64encode(data).decode()
                    images[attachment.file_id] = (
                        f"data:{attachment.file.content_type};base64,{encoded}"
                    )
            allowed = set(images)
            item["texts"] = [
                {
                    "label": TEXT_LABELS[field],
                    "html": _embed_images(
                        richtext.sanitize(getattr(entry, field), image_ids=allowed), images
                    ),
                }
                for field in TEXT_FIELDS
                if getattr(entry, field)
            ]
            item["materials"] = [
                f"{m.get_kind_display()} {m.code} (versão {m.version} do cadastro)"
                for m in entry.materials.filter(removed_at__isnull=True)
            ]
            item["addenda"] = [
                {
                    "number": addendum.number,
                    "author": addendum.author.get_full_name() or addendum.author.username,
                    "at": datetime_br(addendum.created_at),
                    "html": _embed_images(
                        richtext.sanitize(addendum.text, image_ids=allowed), images
                    ),
                }
                for addendum in entry.addenda.select_related("author").order_by("number")
            ]
        items.append(item)
    return items


def attachment_rows(parts, entries) -> list[dict]:
    rows = []
    for part in parts:
        if part.get("kind") != "document":
            continue
        for section in part["content"].get("sections", []):
            for block in section.get("blocks", []):
                if block.get("kind") != "files":
                    continue
                for item in block.get("files", []):
                    rows.append(
                        {
                            "name": item.get("name", ""),
                            "origin": part["toc"],
                            "sha256": item.get("sha256", ""),
                        }
                    )
    for entry in entries:
        for attachment in (
            NotebookEntry.objects.get(pk=entry["id"])
            .attachments.filter(removed_at__isnull=True)
            .select_related("file")
        ):
            rows.append(
                {
                    "name": attachment.file.original_name,
                    "origin": f"Caderno {DASH} entrada {entry['number']}",
                    "sha256": attachment.file.sha256,
                }
            )
    return rows


# ------------------------------------------------------------------ composição


def compose(
    project, *, options: dict, with_financials: bool, pending: list[str], until, final=None
) -> dict:
    history = bool(options.get("historico_versoes"))
    documents = documents_in_order(project)
    parts = []
    if pending:
        parts.append({"kind": "pending", "toc": "Pendências", "items": list(pending)})
    for kind, obj, title in documents:
        parts.extend(
            _document_parts(
                kind,
                obj,
                title=title,
                history=history,
                mask=kind == "business_plan" and not with_financials,
            )
        )
    entries = notebook(project, options.get("caderno"))
    parts.append({"kind": "versions", "toc": "Quadro de versões", "rows": version_rows(documents)})
    parts.append(
        {
            "kind": "final_versions",
            "toc": "Versões do documento final",
            "rows": final_version_rows(project, final),
        }
    )
    parts.append(
        {
            "kind": "audit",
            "toc": "Resumo da trilha de auditoria",
            "summary": audit_summary(project, until),
        }
    )
    parts.append(
        {
            "kind": "notebook",
            "toc": "Histórico do caderno de laboratório",
            "mode": options.get("caderno"),
            "entries": entries,
        }
    )
    parts.append(
        {"kind": "attachments", "toc": "Lista de anexos", "rows": attachment_rows(parts, entries)}
    )
    for number, part in enumerate(parts, start=1):
        part["anchor"] = f"parte-{number}"
    return {
        "parts": parts,
        "options": options,
        "with_financials": with_financials,
        "final_number": final.number if final else 0,
    }


def final_version_rows(project, final) -> list[dict]:
    """Quadro das versões do documento final até a representada (feature 016)."""
    from .models import FinalDocumentVersion

    if final is None:
        return []
    rows = []
    for version in (
        FinalDocumentVersion.objects.filter(project=project, number__lte=final.number)
        .select_related("registered_by")
        .order_by("number")
    ):
        rows.append(
            {
                "version": version.number_display,
                "date": datetime_br(version.created_at),
                "by": (version.registered_by.get_full_name() or version.registered_by.username)
                if version.registered_by
                else "—",
                "changes": version.changes_text or "—",
                "reason": version.get_reason_display(),
            }
        )
    return rows


def composition_digest(project, composition: dict, *, layout_id: int, pending: list[str]) -> str:
    """Resumo do que muda o conteúdo (research R10); a trilha resumida não entra."""
    parts = [["documento_final", composition.get("final_number", 0)]]
    for part in composition["parts"]:
        if part["kind"] == "document":
            parts.append(
                [
                    part["doc_kind"],
                    part["object_id"],
                    part["version"],
                    part["content_hash"],
                    part["superseded"],
                    part["masked"],
                ]
            )
        elif part["kind"] == "notebook":
            parts.append(
                [
                    "caderno",
                    part["mode"],
                    [
                        [e["id"], e["status"], [s["hash"] for s in e["signatures"]]]
                        for e in part["entries"]
                    ],
                ]
            )
    return content_hash(
        {
            "projeto": project.pk,
            "versao": project.version or 0,
            "opcoes": composition["options"],
            "financeiro": composition["with_financials"],
            "layout": layout_id,
            "pendencias": pending,
            "partes": parts,
        }
    )
