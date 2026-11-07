"""Ciclo de revisão e assinatura eletrônica (FR-001 a FR-016 da feature 005).

A reautenticação acontece antes das transações do serviço, para que as tentativas e os alertas de
falha fiquem gravados mesmo quando a operação é recusada.
"""

from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from sgp.accounts.profiles import Profile, active_profiles
from sgp.audit.services import record_event
from sgp.core.access import can_access_project
from sgp.files.storage import IntegrityFailure, read_verified

from .canonical import content_hash, normalized
from .documents import APPROVED, EDITABLE, IN_REVIEW, RETURNED, get_adapter
from .models import (
    ApprovalDelegation,
    ApprovedVersion,
    DocumentKind,
    Meaning,
    ReviewComment,
    Signature,
)
from .reauth import reauthenticate

DELEGATE_PROFILES = frozenset({Profile.RD_MANAGER, Profile.PROJECT_LEADER, Profile.QUALITY})
MAX_DELEGATION_DAYS = 30


# ------------------------------------------------------------------ utilidades


def _event(event_type: str, adapter, obj, by, **kwargs):
    return record_event(
        event_type,
        actor=by,
        object_type=f"signatures.{adapter.kind}",
        object_id=str(obj.pk),
        object_repr=adapter.title(obj),
        project_id=adapter.project(obj).pk,
        **kwargs,
    )


def signatures_of(adapter, obj, version=None):
    return Signature.objects.filter(
        kind=adapter.kind, object_id=obj.pk, version=version or adapter.version(obj)
    ).select_related("signer", "delegation__delegator")


def elaborated_signature(adapter, obj) -> Signature | None:
    return (
        signatures_of(adapter, obj)
        .filter(meaning=Meaning.ELABORATED)
        .order_by("-signed_at", "-pk")
        .first()
    )


def active_delegation(user, day=None) -> ApprovalDelegation | None:
    day = day or timezone.localdate()
    return (
        ApprovalDelegation.objects.filter(
            delegate=user, ended_at__isnull=True, starts_on__lte=day, ends_on__gte=day
        )
        .select_related("delegator")
        .first()
    )


def is_approver(user) -> bool:
    return Profile.RD_MANAGER in active_profiles(user) or active_delegation(user) is not None


def can_approve(user, adapter, obj) -> bool:
    if not is_approver(user) or not can_access_project(user, adapter.project(obj)):
        return False
    elaborated = elaborated_signature(adapter, obj)
    return elaborated is None or elaborated.signer_id != user.pk


def _sign(adapter, obj, by, meaning: str, digest: str, delegation=None) -> Signature:
    signature = Signature.objects.create(
        kind=adapter.kind,
        object_id=obj.pk,
        project=adapter.project(obj),
        version=adapter.version(obj),
        content_hash=digest,
        meaning=meaning,
        signer=by,
        signer_name=by.get_full_name() or by.username,
        signer_title=getattr(by, "job_title", "") or "",
        delegation=delegation,
    )
    _event(
        "signatures.signed",
        adapter,
        obj,
        by,
        new_value={
            "versao": signature.version,
            "significado": signature.get_meaning_display(),
            "resumo": digest,
            "delegacao": delegation.pk if delegation else None,
        },
    )
    return signature


def _approval_delegation(by):
    if Profile.RD_MANAGER in active_profiles(by):
        return None
    return active_delegation(by)


# --------------------------------------------------------------- ciclo do documento


def submit(kind: str, obj, *, by, password: str, request=None):
    """Envia para revisão com a assinatura "elaborado" (FR-002)."""
    adapter = get_adapter(kind)
    obj = adapter.get(obj.pk)
    if not adapter.can_edit(by, obj):
        raise ValidationError("Você não pode enviar este documento para revisão.")
    missing = adapter.completeness(obj)
    if missing:
        raise ValidationError(missing)
    reauthenticate(request, by, password)
    with transaction.atomic():
        obj = adapter.lock(obj)
        if adapter.status(obj) not in EDITABLE:
            raise ValidationError("O documento não está em rascunho nem devolvido.")
        previous = adapter.status(obj)
        digest = content_hash(adapter.snapshot(obj))
        adapter.set_status(obj, IN_REVIEW)
        _sign(adapter, obj, by, Meaning.ELABORATED, digest)
        _event(
            "signatures.submitted",
            adapter,
            obj,
            by,
            old_value={"situacao": previous},
            new_value={"situacao": IN_REVIEW, "versao": adapter.version(obj), "resumo": digest},
        )
    return obj


def sign_review(kind: str, obj, *, by, password: str, request=None) -> Signature:
    """Assinatura "revisado" de terceiro, sem mudar a situação (FR-009)."""
    adapter = get_adapter(kind)
    obj = adapter.get(obj.pk)
    if adapter.status(obj) != IN_REVIEW:
        raise ValidationError("Só documentos em revisão recebem a assinatura de revisão.")
    if not can_access_project(by, adapter.project(obj)) or not active_profiles(by):
        raise ValidationError("Você não tem acesso a este documento.")
    elaborated = elaborated_signature(adapter, obj)
    if elaborated is not None and elaborated.signer_id == by.pk:
        raise ValidationError("Quem elaborou não assina como revisor.")
    reauthenticate(request, by, password)
    with transaction.atomic():
        obj = adapter.lock(obj)
        digest = content_hash(adapter.snapshot(obj))
        return _sign(adapter, obj, by, Meaning.REVIEWED, digest)


def return_document(kind: str, obj, *, by, comment: str):
    """Devolução com comentário obrigatório; volta a editável (FR-003)."""
    adapter = get_adapter(kind)
    obj = adapter.get(obj.pk)
    comment = (comment or "").strip()
    if not comment:
        raise ValidationError("Informe o comentário da devolução.")
    if not is_approver(by) or not can_access_project(by, adapter.project(obj)):
        raise ValidationError("Só o Gestor de P&D ou quem tem delegação devolve documentos.")
    with transaction.atomic():
        obj = adapter.lock(obj)
        if adapter.status(obj) != IN_REVIEW:
            raise ValidationError("O documento não está em revisão.")
        adapter.set_status(obj, RETURNED)
        ReviewComment.objects.create(
            kind=adapter.kind,
            object_id=obj.pk,
            project=adapter.project(obj),
            version=adapter.version(obj),
            author=by,
            text=comment,
        )
        _event(
            "signatures.returned",
            adapter,
            obj,
            by,
            old_value={"situacao": IN_REVIEW},
            new_value={"situacao": RETURNED},
            reason=comment,
        )
    return obj


def _freeze(adapter, obj, by, content, digest) -> ApprovedVersion:
    return ApprovedVersion.objects.create(
        kind=adapter.kind,
        object_id=obj.pk,
        project=adapter.project(obj),
        version=adapter.version(obj),
        content=normalized(content),
        content_hash=digest,
        approved_by=by,
    )


def approve(kind: str, obj, *, by, password: str, request=None):
    """Aprovação com assinatura "aprovado" sobre o mesmo conteúdo do elaborador (FR-004)."""
    adapter = get_adapter(kind)
    obj = adapter.get(obj.pk)
    if kind != DocumentKind.SUBDOCUMENT and adapter.project(obj).status != "open":
        raise ValidationError(
            "TAP e Plano de Negócios do projeto em abertura são aprovados com o projeto."
        )
    if not is_approver(by) or not can_access_project(by, adapter.project(obj)):
        raise ValidationError("Só o Gestor de P&D ou quem tem delegação aprova documentos.")
    elaborated = elaborated_signature(adapter, obj)
    if elaborated is not None and elaborated.signer_id == by.pk:
        raise ValidationError("Quem elaborou não pode aprovar o mesmo documento.")
    if signatures_of(adapter, obj).filter(meaning=Meaning.REVIEWED, signer=by).exists():
        raise ValidationError("Quem assinou como revisor não aprova a mesma versão (FR-009).")
    missing = adapter.completeness(obj)
    if missing:
        raise ValidationError(missing)
    reauthenticate(request, by, password)
    with transaction.atomic():
        obj = adapter.lock(obj)
        if adapter.status(obj) != IN_REVIEW:
            raise ValidationError("O documento não está em revisão.")
        content = adapter.snapshot(obj)
        digest = content_hash(content)
        if elaborated is None or elaborated.content_hash != digest:
            raise ValidationError(
                "O conteúdo mudou depois da assinatura de quem elaborou; devolva para nova assinatura."
            )
        _sign(adapter, obj, by, Meaning.APPROVED, digest, delegation=_approval_delegation(by))
        _freeze(adapter, obj, by, content, digest)
        adapter.set_status(obj, APPROVED)
        adapter.on_approved(obj, by)
        _event(
            "signatures.approved",
            adapter,
            obj,
            by,
            new_value={"versao": adapter.version(obj), "resumo": digest},
        )
    return obj


def new_version(kind: str, obj, *, by, reason: str):
    """Versão seguinte em rascunho a partir do aprovado, com motivo (FR-005)."""
    adapter = get_adapter(kind)
    obj = adapter.get(obj.pk)
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError("Informe o motivo da nova versão.")
    if not adapter.can_create_version(by, obj):
        raise ValidationError("Você não pode criar nova versão deste documento.")
    with transaction.atomic():
        obj = adapter.lock(obj)
        if adapter.status(obj) != APPROVED:
            raise ValidationError(
                "Só documento aprovado ganha nova versão; termine a versão em andamento."
            )
        before = adapter.version(obj)
        adapter.bump_version(obj)
        _event(
            "signatures.new_version",
            adapter,
            obj,
            by,
            old_value={"versao": before},
            new_value={"versao": adapter.version(obj)},
            reason=reason,
        )
    return obj


# ------------------------------------------------------------------ integridade


def versions_of(adapter, obj) -> list[ApprovedVersion]:
    versions = list(
        ApprovedVersion.objects.filter(kind=adapter.kind, object_id=obj.pk).order_by("version")
    )
    latest = versions[-1].version if versions else None
    for item in versions:
        item.superseded = item.version != latest or adapter.version(obj) != latest
    return versions


def verify(kind: str, obj, *, by) -> dict:
    """Recalcula o resumo de cada versão aprovada e confere assinaturas, conteúdo e anexos (FR-011)."""
    from sgp.files.models import StoredFile

    adapter = get_adapter(kind)
    obj = adapter.get(obj.pk)
    problems = []
    versions = versions_of(adapter, obj)
    for item in versions:
        name = f"versão {item.version_display}"
        if content_hash(item.content) != item.content_hash:
            problems.append(f"{name}: o conteúdo guardado não confere com o resumo aprovado.")
        signatures = list(
            Signature.objects.filter(kind=adapter.kind, object_id=obj.pk, version=item.version)
        )
        # Rodadas anteriores a uma devolução assinaram outro conteúdo e ficam como histórico;
        # a versão aprovada precisa de uma assinatura "elaborado" e da "aprovado" sobre ela.
        for meaning, label in ((Meaning.ELABORATED, "elaborado"), (Meaning.APPROVED, "aprovado")):
            if not any(
                s.meaning == meaning and s.content_hash == item.content_hash for s in signatures
            ):
                problems.append(
                    f"{name}: falta assinatura {label} que confira com o conteúdo aprovado."
                )
        for signature in signatures:
            if (
                signature.meaning == Meaning.APPROVED
                and signature.content_hash != item.content_hash
            ):
                problems.append(
                    f"{name}: assinatura aprovado de {signature.signer_name} não confere com "
                    "o conteúdo aprovado."
                )
        for attachment in item.content.get("anexos", []):
            stored = StoredFile.objects.filter(pk=attachment.get("id")).first()
            if stored is None or stored.sha256 != attachment.get("sha256"):
                problems.append(
                    f"{name}: anexo {attachment.get('nome')} não confere com o registro."
                )
                continue
            try:
                read_verified(stored)
            except IntegrityFailure:
                problems.append(
                    f"{name}: anexo {attachment.get('nome')} alterado no armazenamento."
                )
    if (
        versions
        and adapter.status(obj) == APPROVED
        and adapter.version(obj) == versions[-1].version
    ):
        current = normalized(adapter.comparable(adapter.snapshot(obj)))
        if current != adapter.comparable(versions[-1].content):
            problems.append("O conteúdo atual do documento difere da versão aprovada.")
    result = {"integro": not problems, "problemas": problems, "versoes": len(versions)}
    _event("signatures.verified", adapter, obj, by, new_value=result)
    return result


# ------------------------------------------------------------------- delegação


def create_delegation(*, by, delegate, starts_on, ends_on, reason: str) -> ApprovalDelegation:
    reason = (reason or "").strip()
    if Profile.RD_MANAGER not in active_profiles(by):
        raise ValidationError("Só o Gestor de P&D delega a aprovação.")
    if not reason:
        raise ValidationError("Informe o motivo da delegação.")
    if delegate.pk == by.pk:
        raise ValidationError("Escolha outra pessoa para a delegação.")
    if not active_profiles(delegate) & DELEGATE_PROFILES:
        raise ValidationError(
            "O delegado precisa ter perfil Gestor de P&D, Líder de projeto ou Qualidade/AR."
        )
    if ends_on < starts_on:
        raise ValidationError("O fim da delegação não pode ser antes do início.")
    if (ends_on - starts_on) > timedelta(days=MAX_DELEGATION_DAYS - 1):
        raise ValidationError(f"A delegação pode durar até {MAX_DELEGATION_DAYS} dias.")
    with transaction.atomic():
        delegation = ApprovalDelegation.objects.create(
            delegator=by, delegate=delegate, starts_on=starts_on, ends_on=ends_on, reason=reason
        )
        record_event(
            "signatures.delegation_created",
            actor=by,
            obj=delegation,
            new_value={"delegado": delegate.username, "inicio": starts_on, "fim": ends_on},
            reason=reason,
        )
    return delegation


def end_delegation(delegation: ApprovalDelegation, *, by, reason: str) -> ApprovalDelegation:
    reason = (reason or "").strip()
    if Profile.RD_MANAGER not in active_profiles(by):
        raise ValidationError("Só o Gestor de P&D encerra delegações.")
    if not reason:
        raise ValidationError("Informe o motivo do encerramento.")
    with transaction.atomic():
        delegation = ApprovalDelegation.objects.select_for_update().get(pk=delegation.pk)
        if delegation.ended_at is not None:
            raise ValidationError("A delegação já foi encerrada.")
        delegation.ended_at = timezone.now()
        delegation.ended_by = by
        delegation.end_reason = reason
        delegation.save(update_fields=["ended_at", "ended_by", "end_reason"])
        record_event(
            "signatures.delegation_ended",
            actor=by,
            obj=delegation,
            old_value={"delegado": delegation.delegate.username, "fim": delegation.ends_on},
            new_value={"encerrada_em": delegation.ended_at},
            reason=reason,
        )
    return delegation


# ----------------------------------------------------------------------- fila


def review_queue(user) -> list[dict]:
    """Documentos em revisão que a pessoa pode aprovar, com os dias de espera (FR-014)."""
    from sgp.projects.models import BusinessPlan, ProjectCharter
    from sgp.subdocuments.models import Subdocument

    rows = []
    today = timezone.localdate()
    sources = (
        (
            DocumentKind.SUBDOCUMENT,
            Subdocument.objects.filter(status=IN_REVIEW).select_related(
                "project", "subdocument_type"
            ),
        ),
        (
            DocumentKind.CHARTER,
            ProjectCharter.objects.filter(doc_status=IN_REVIEW).select_related("project"),
        ),
        (
            DocumentKind.BUSINESS_PLAN,
            BusinessPlan.objects.filter(doc_status=IN_REVIEW).select_related("project"),
        ),
    )
    for kind, queryset in sources:
        adapter = get_adapter(kind)
        for obj in queryset:
            if not can_approve(user, adapter, obj):
                continue
            elaborated = elaborated_signature(adapter, obj)
            since = elaborated.signed_at if elaborated else timezone.now()
            days = (today - timezone.localtime(since).date()).days
            rows.append(
                {
                    "kind": kind,
                    "adapter": adapter,
                    "obj": obj,
                    "title": adapter.title(obj),
                    "project": adapter.project(obj),
                    "since": since,
                    "days": days,
                    "overdue": days > settings.REVIEW_ALERT_DAYS,
                }
            )
    return sorted(rows, key=lambda row: row["since"])


# ------------------------------------------------------------- TAP e Plano (002)


def _project_documents(project):
    return (
        (get_adapter(DocumentKind.CHARTER), project.charter),
        (get_adapter(DocumentKind.BUSINESS_PLAN), project.business_plan),
    )


def submit_project(project, *, by, password: str, request=None):
    """Submissão do projeto com a assinatura "elaborado" do líder no TAP e no Plano (FR-012)."""
    from sgp.projects import workflow

    reauthenticate(request, by, password)
    with transaction.atomic():
        project = workflow.submit(project, by=by)
        for adapter, obj in _project_documents(project):
            obj = adapter.lock(obj)
            digest = content_hash(adapter.snapshot(obj))
            _sign(adapter, obj, by, Meaning.ELABORATED, digest)
            _event(
                "signatures.submitted",
                adapter,
                obj,
                by,
                new_value={"situacao": IN_REVIEW, "versao": adapter.version(obj), "resumo": digest},
            )
    return project


def return_project(project, *, by, comment: str):
    from sgp.projects import workflow

    with transaction.atomic():
        project = workflow.return_project(project, by=by, comment=comment)
        for adapter, obj in _project_documents(project):
            obj = adapter.lock(obj)
            ReviewComment.objects.create(
                kind=adapter.kind,
                object_id=obj.pk,
                project=project,
                version=adapter.version(obj),
                author=by,
                text=comment.strip(),
            )
    return project


def approve_project(project, *, by, password: str, request=None):
    """Aprovação do projeto com a assinatura "aprovado" no TAP e no Plano (FR-012)."""
    from sgp.projects import workflow

    reauthenticate(request, by, password)
    with transaction.atomic():
        checked = []
        for adapter, obj in _project_documents(project):
            obj = adapter.lock(obj)
            content = adapter.snapshot(obj)
            digest = content_hash(content)
            elaborated = elaborated_signature(adapter, obj)
            if elaborated is None or elaborated.content_hash != digest:
                raise ValidationError(
                    f"{adapter.label}: o conteúdo mudou depois da assinatura do líder; devolva o projeto."
                )
            checked.append((adapter, obj, content, digest))
        project = workflow.approve(project, by=by)
        for adapter, obj, content, digest in checked:
            _sign(adapter, obj, by, Meaning.APPROVED, digest, delegation=_approval_delegation(by))
            _freeze(adapter, obj, by, content, digest)
            _event(
                "signatures.approved",
                adapter,
                obj,
                by,
                new_value={"versao": adapter.version(obj), "resumo": digest},
            )
    return project


def block_context(user, kind: str, obj) -> dict:
    """Dados do bloco de assinaturas e das ações possíveis para a pessoa (telas dos documentos)."""
    adapter = get_adapter(kind)
    status = adapter.status(obj)
    project_open = adapter.project(obj).status == "open"
    in_cycle = kind == DocumentKind.SUBDOCUMENT or project_open
    elaborated = elaborated_signature(adapter, obj)
    return {
        "kind": kind,
        "obj": obj,
        "version": adapter.version(obj),
        "status": status,
        "signatures": signatures_of(adapter, obj),
        "versions": versions_of(adapter, obj),
        "approver_label": adapter.approver_label(obj),
        "can_submit": in_cycle and adapter.can_edit(user, obj),
        "can_approve": in_cycle and status == IN_REVIEW and can_approve(user, adapter, obj),
        "can_review": status == IN_REVIEW
        and (elaborated is None or elaborated.signer_id != user.pk)
        and can_access_project(user, adapter.project(obj)),
        "can_new_version": in_cycle
        and status == APPROVED
        and adapter.can_create_version(user, obj),
    }
