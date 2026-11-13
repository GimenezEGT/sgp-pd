"""Reconstrução das versões do documento final a partir das aprovações registradas (FR-009 da
feature 016). Recebe o registro de modelos (`apps`), para servir à migração e aos testes."""

import hashlib
import json
from datetime import timedelta

CHARTER_TITLE = "Termo de Abertura do Projeto"
PLAN_TITLE = "Plano de Negócios"
CHANGE = "alteracao"
GROUP_WINDOW = timedelta(seconds=5)
REASON = "reconstruction"
TRAIL_NOTE = "Reconstrução a partir das aprovações registradas (feature 016)"


def _digest(entries: list[dict]) -> str:
    canonical = sorted([e["tipo"], e["id"], e["versao"], e["resumo"]] for e in entries)
    data = json.dumps(canonical, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _groups(approvals) -> list[list]:
    """Aprovações do mesmo aprovador com menos de 5 segundos de diferença formam uma versão."""
    groups = []
    for approval in approvals:
        current = groups[-1] if groups else None
        if (
            current
            and current[0].approved_by_id == approval.approved_by_id
            and approval.approved_at - current[0].approved_at < GROUP_WINDOW
        ):
            current.append(approval)
        else:
            groups.append([approval])
    return groups


def _label(approval, subs) -> str:
    if approval.kind == "charter":
        return CHARTER_TITLE
    if approval.kind == "business_plan":
        return PLAN_TITLE
    sub = subs.get(approval.object_id)
    if sub is None:
        return f"Subdocumento {approval.object_id}"
    term = sub.subdocument_type
    return f"{term.label} {sub.sequence}" if term.code == CHANGE else term.label


def _position(entry, subs, order) -> tuple:
    """Ordem do documento completo: TAP, Plano de Negócios e subdocumentos na ordem do fluxo."""
    if entry["tipo"] == "charter":
        return (0, 0, entry["aprovada_em"])
    if entry["tipo"] == "business_plan":
        return (1, 0, entry["aprovada_em"])
    sub = subs.get(entry["id"])
    code = sub.subdocument_type.code if sub else ""
    if code == CHANGE:
        rank = order.index("verificacao-final") if "verificacao-final" in order else 99
        return (2, rank - 0.5, entry["aprovada_em"])
    return (2, order.index(code) if code in order else 99, entry["aprovada_em"])


def rebuild(apps, flow: list[str] | None = None) -> int:
    """Cria as versões reconstruídas dos projetos que ainda não têm nenhuma; devolve quantas."""
    from sgp.subdocuments.flow import FLOW

    order = list(flow or FLOW)
    Project = apps.get_model("projects", "Project")
    ApprovedVersion = apps.get_model("signatures", "ApprovedVersion")
    Subdocument = apps.get_model("subdocuments", "Subdocument")
    FinalDocumentVersion = apps.get_model("fulldoc", "FinalDocumentVersion")
    created = 0
    for project in Project.objects.all().order_by("pk"):
        if FinalDocumentVersion.objects.filter(project_id=project.pk).exists():
            continue
        approvals = list(
            ApprovedVersion.objects.filter(project_id=project.pk).order_by("approved_at", "pk")
        )
        if not approvals:
            continue
        subs = {
            sub.pk: sub
            for sub in Subdocument.objects.filter(project_id=project.pk).select_related(
                "subdocument_type"
            )
        }

        state: dict = {}
        number = 0
        for group in _groups(approvals):
            changes = []
            for approval in group:
                key = (approval.kind, approval.object_id)
                before = state.get(key)
                entry = {
                    "tipo": approval.kind,
                    "id": approval.object_id,
                    "parte": _label(approval, subs),
                    "versao": approval.version,
                    "aprovada_em": approval.approved_at.isoformat(),
                    "resumo": approval.content_hash,
                }
                changes.append(
                    {
                        "tipo": approval.kind,
                        "id": approval.object_id,
                        "parte": entry["parte"],
                        "de": before["versao"] if before else None,
                        "para": approval.version,
                        "aprovada_em": entry["aprovada_em"],
                    }
                )
                state[key] = entry
            number += 1
            entries = sorted(state.values(), key=lambda e, s=subs: _position(e, s, order))
            FinalDocumentVersion.objects.create(
                project_id=project.pk,
                number=number,
                created_at=group[0].approved_at,
                registered_by_id=group[0].approved_by_id,
                reason=REASON,
                changes=changes,
                composition=entries,
                composition_hash=_digest(entries),
            )
            created += 1
    return created


def record_missing_events() -> int:
    """Evento na trilha para cada versão reconstruída que ainda não tem.

    O evento é gravado no momento em que a reconstrução é registrada (a trilha não aceita data
    passada); a data e o aprovador originais vão no valor do evento. Roda depois das migrações,
    com os modelos atuais, e não repete eventos já gravados.
    """
    from django.db import transaction

    from sgp.audit.models import AuditEvent
    from sgp.audit.services import record_event

    from .models import FinalDocumentVersion, change_text

    recorded = set(
        AuditEvent.objects.filter(
            event_type="fulldoc.version_created", object_type="fulldoc.finaldocumentversion"
        ).values_list("object_id", flat=True)
    )
    count = 0
    with transaction.atomic():
        versions = (
            FinalDocumentVersion.objects.filter(reason=REASON)
            .select_related("project", "registered_by")
            .order_by("project_id", "number")
        )
        for version in versions:
            if str(version.pk) in recorded:
                continue
            approver = version.registered_by
            record_event(
                "fulldoc.version_created",
                actor=None,
                obj=version,
                project_id=version.project_id,
                new_value={
                    "versao": version.number,
                    "motivo": version.reason,
                    "mudancas": [change_text(change) for change in version.changes],
                    "resumo_composicao": version.composition_hash,
                    "partes": len(version.composition),
                    "aprovada_em": version.created_at.isoformat(),
                    "aprovada_por": approver.username if approver else "",
                },
                reason=TRAIL_NOTE,
            )
            count += 1
    return count
