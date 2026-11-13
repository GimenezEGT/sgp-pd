"""Versões do documento final do projeto (feature 016).

O documento final é o documento completo da feature 009, composto pelas partes aprovadas (TAP,
Plano de Negócios e subdocumentos). Cada aprovação de parte registra a versão seguinte, com a
mudança e a composição completa, na mesma transação da aprovação.
"""

import hashlib
import json

from django.db import transaction

from sgp.audit.models import AuditEvent
from sgp.audit.services import record_event
from sgp.signatures.models import ApprovedVersion

from .models import FinalDocumentVersion, FinalVersionReason, change_text


def composition(project) -> list[dict]:
    """Cada parte na versão aprovada mais recente, na ordem do documento completo."""
    from .compose import documents_in_order

    entries = []
    for kind, obj, title in documents_in_order(project):
        approval = (
            ApprovedVersion.objects.filter(kind=kind, object_id=obj.pk).order_by("-version").first()
        )
        if approval is None:
            continue
        entries.append(
            {
                "tipo": kind,
                "id": obj.pk,
                "parte": title,
                "versao": approval.version,
                "aprovada_em": approval.approved_at.isoformat(),
                "resumo": approval.content_hash,
            }
        )
    return entries


def digest(entries: list[dict]) -> str:
    """Resumo da composição, independente da ordem de exibição."""
    canonical = sorted([e["tipo"], e["id"], e["versao"], e["resumo"]] for e in entries)
    data = json.dumps(canonical, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def latest(project) -> FinalDocumentVersion | None:
    return FinalDocumentVersion.objects.filter(project=project).order_by("-number").first()


def history(project) -> list[FinalDocumentVersion]:
    return list(
        FinalDocumentVersion.objects.filter(project=project)
        .select_related("registered_by")
        .order_by("number")
    )


def _lock(project) -> None:
    from sgp.projects.models import Project

    Project.objects.select_for_update().filter(pk=project.pk).first()


def _create(project, *, by, reason, changes, entries) -> FinalDocumentVersion:
    previous = latest(project)
    version = FinalDocumentVersion.objects.create(
        project=project,
        number=(previous.number + 1) if previous else 1,
        registered_by=by,
        reason=reason,
        changes=changes,
        composition=entries,
        composition_hash=digest(entries),
    )
    record_event(
        "fulldoc.version_created",
        actor=by,
        obj=version,
        project_id=project.pk,
        new_value={
            "versao": version.number,
            "motivo": reason,
            "mudancas": [change_text(change) for change in changes],
            "resumo_composicao": version.composition_hash,
            "partes": len(entries),
        },
    )
    return version


def register(project, *, by, approvals) -> FinalDocumentVersion | None:
    """Nova versão do documento final pela aprovação de uma ou mais partes (FR-003)."""
    with transaction.atomic():
        _lock(project)
        entries = composition(project)
        if not entries:
            return None
        previous = latest(project)
        before = {(e["tipo"], e["id"]): e for e in (previous.composition if previous else [])}
        labels = {(e["tipo"], e["id"]): e["parte"] for e in entries}
        changes = []
        for approval in approvals:
            key = (approval.kind, approval.object_id)
            old = before.get(key)
            changes.append(
                {
                    "tipo": approval.kind,
                    "id": approval.object_id,
                    "parte": labels.get(key, approval.kind),
                    "de": old["versao"] if old else None,
                    "para": approval.version,
                    "aprovada_em": approval.approved_at.isoformat(),
                }
            )
        return _create(
            project, by=by, reason=FinalVersionReason.APPROVAL, changes=changes, entries=entries
        )


def ensure_current(project, *, by) -> FinalDocumentVersion | None:
    """Versão registrada que corresponde à composição vigente; registra a que falta (FR-010)."""
    with transaction.atomic():
        _lock(project)
        entries = composition(project)
        if not entries:
            return None
        previous = latest(project)
        if previous is not None and previous.composition_hash == digest(entries):
            return previous
        before = {(e["tipo"], e["id"]): e for e in (previous.composition if previous else [])}
        changes = [
            {
                "tipo": e["tipo"],
                "id": e["id"],
                "parte": e["parte"],
                "de": before[(e["tipo"], e["id"])]["versao"]
                if (e["tipo"], e["id"]) in before
                else None,
                "para": e["versao"],
                "aprovada_em": e["aprovada_em"],
            }
            for e in entries
            if (e["tipo"], e["id"]) not in before
            or before[(e["tipo"], e["id"])]["resumo"] != e["resumo"]
            or before[(e["tipo"], e["id"])]["versao"] != e["versao"]
        ]
        return _create(
            project,
            by=by,
            reason=FinalVersionReason.RECOMPOSITION,
            changes=changes,
            entries=entries,
        )


def part_history(kind: str, obj) -> list[dict]:
    """Histórico de versões de uma parte e as versões do documento final em que entrou (FR-008)."""
    from sgp.signatures.documents import STATUS_LABELS, get_adapter

    adapter = get_adapter(kind)
    current = adapter.version(obj)
    status = adapter.status(obj)
    approvals = {
        a.version: a
        for a in ApprovedVersion.objects.filter(kind=kind, object_id=obj.pk).select_related(
            "approved_by"
        )
    }
    last_approved = max(approvals) if approvals else None
    opened = {
        (event.new_value or {}).get("versao"): event
        for event in AuditEvent.objects.filter(
            event_type="signatures.new_version",
            object_type=f"signatures.{kind}",
            object_id=str(obj.pk),
        ).select_related("actor")
    }
    finals = FinalDocumentVersion.objects.filter(project=adapter.project(obj)).order_by("number")
    rows = []
    for number in range(1, current + 1):
        approval = approvals.get(number)
        if approval is not None:
            situation = "Vigente" if number == last_approved else "Substituída"
        elif number == current:
            situation = STATUS_LABELS.get(status, status)
        else:
            situation = "Sem aprovação"
        event = opened.get(number)
        if number == 1:
            creator = getattr(obj, "created_by", None) or getattr(
                adapter.project(obj), "created_by", None
            )
            opened_by = _person(creator)
            opened_at = getattr(obj, "created_at", None) or adapter.project(obj).created_at
            reason = "Criação"
        else:
            opened_by = (
                _person(event.actor)
                if event and event.actor_id
                else (event.actor_username if event else "—")
            )
            opened_at = event.occurred_at if event else None
            reason = event.reason if event else "—"
        rows.append(
            {
                "number": f"{number:02d}",
                "situation": situation,
                "opened_by": opened_by,
                "opened_at": opened_at,
                "reason": reason,
                "approved_by": _person(approval.approved_by) if approval else "",
                "approved_at": approval.approved_at if approval else None,
                "finals": [
                    final.number_display
                    for final in finals
                    if any(
                        c["tipo"] == kind and c["id"] == obj.pk and c["versao"] == number
                        for c in final.composition
                    )
                ],
            }
        )
    return rows


def _person(user) -> str:
    if user is None:
        return "—"
    return user.get_full_name() or user.username
