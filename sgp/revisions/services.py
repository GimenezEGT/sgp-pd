"""Revisão controlada dos modelos (FR-002 a FR-019 da feature 013).

A Qualidade/AR abre (pelas telas das features 004 e 006), altera, envia e descarta; o Gestor de
P&D devolve ou aprova com assinatura e vigência; publicar é efeito da aprovação.
"""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from sgp.accounts.profiles import Profile, active_profiles
from sgp.audit.services import record_event
from sgp.signatures.reauth import reauthenticate

from . import diff
from .adapters import ADAPTERS, digest, get_adapter
from .models import (
    RetirementStatus,
    ReviewStatus,
    SignaturePurpose,
    Step,
    TemplateKind,
    TemplateRetirement,
    TemplateSignature,
    TemplateStep,
)

NOT_QUALITY = "Só a Qualidade/AR elabora, envia e descarta revisões de modelos."
NOT_MANAGER = "Só o Gestor de P&D aprova ou devolve revisões de modelos."
NOT_EDITING = "A revisão foi enviada para aprovação e não muda; aguarde a decisão ou a devolução."
SITUATIONS = {
    "editing": "Rascunho",
    "submitted": "Enviada para aprovação",
    "pending": "Aprovada aguardando vigência",
    "current": "Vigente",
    "superseded": "Substituída",
    "discarded": "Descartada",
}


def _require(by, profile, message):
    if profile not in active_profiles(by):
        raise ValidationError(message)


def _event(event_type, obj, by, *, request=None, **kwargs):
    return record_event(event_type, actor=by, obj=obj, request=request, **kwargs)


def record_step(adapter, obj, step, actor=None, comment: str = "") -> TemplateStep:
    return TemplateStep.objects.create(
        kind=adapter.kind,
        template_id=obj.pk,
        version=adapter.version(obj),
        family=adapter.family(obj),
        step=step,
        actor=actor,
        comment=comment,
    )


# ------------------------------------------------------------------ situação


def situation(adapter, obj, current=None) -> str:
    if obj.status == "discarded":
        return "discarded"
    if obj.status == "draft":
        return obj.review_status
    if obj.valid_from > timezone.localdate():
        return "pending"
    current = current if current is not None else adapter.current(obj)
    return "current" if current and current.pk == obj.pk else "superseded"


def in_progress(adapter, obj):
    """Revisão em andamento da família: rascunho, enviada ou aprovada aguardando vigência (FR-006)."""
    today = timezone.localdate()
    for version in adapter.versions(obj):
        if version.status == "draft" or (
            version.status == "published" and version.valid_from > today
        ):
            return version
    return None


def ensure_can_open(kind: str, family_obj) -> None:
    """Chamado ao abrir revisão (telas das features 004 e 006)."""
    adapter = get_adapter(kind)
    if kind == TemplateKind.FORM and is_retired(family_obj.subdocument_type):
        raise ValidationError("Este modelo foi retirado de uso e não recebe nova revisão.")
    pending = in_progress(adapter, family_obj)
    if pending is not None and pending.status == "published":
        raise ValidationError(
            f"A versão {pending.version_display} está aprovada aguardando vigência; "
            "abra a próxima revisão depois que ela entrar em vigência."
        )


def opened(kind: str, obj, by) -> None:
    record_step(get_adapter(kind), obj, Step.OPENED, by)


def require_editing(obj) -> None:
    if obj.status == "draft" and obj.review_status != ReviewStatus.EDITING:
        raise ValidationError(NOT_EDITING)


def baseline(adapter, obj):
    """Versão de referência da comparação: a vigente ou, sem vigente, a última publicada."""
    current = adapter.current(obj)
    if current is not None and current.pk != obj.pk:
        return current
    return next(
        (v for v in adapter.versions(obj) if v.status == "published" and v.pk != obj.pk), None
    )


def compare(adapter, old, new) -> dict:
    return diff.compare(adapter.comparable(old) if old else {}, adapter.comparable(new))


# ------------------------------------------------------------------ ciclo


def submit(kind: str, obj, *, by, reason: str, impact: str, request=None):
    adapter = get_adapter(kind)
    _require(by, Profile.QUALITY, NOT_QUALITY)
    reason, impact = (reason or "").strip(), (impact or "").strip()
    with transaction.atomic():
        obj = adapter.lock(obj)
        if obj.status != "draft":
            raise ValidationError("Só rascunho de revisão é enviado para aprovação.")
        require_editing(obj)
        problems = []
        if not reason:
            problems.append("Informe o motivo da revisão.")
        if not impact:
            problems.append("Descreva o impacto esperado.")
        problems += adapter.errors(obj)
        changes = compare(adapter, baseline(adapter, obj), obj)
        if diff.is_empty(changes):
            problems.append("A revisão não muda nada em relação à versão vigente.")
        if problems:
            raise ValidationError(problems)
        obj.review_status = ReviewStatus.SUBMITTED
        obj.revision_reason, obj.revision_impact = reason, impact
        obj.submitted_by, obj.submitted_at = by, timezone.now()
        obj.save(
            update_fields=[
                "review_status",
                "revision_reason",
                "revision_impact",
                "submitted_by",
                "submitted_at",
            ]
        )
        record_step(adapter, obj, Step.SUBMITTED, by, reason)
        count = sum(len(changes[key]) for key in ("added", "removed", "changed"))
        _event(
            "templates.submitted",
            obj,
            by,
            request=request,
            new_value={
                "versao": adapter.version(obj),
                "motivo": reason,
                "impacto": impact,
                "mudancas": count,
            },
        )
    return obj


def _require_decider(adapter, obj, by):
    _require(by, Profile.RD_MANAGER, NOT_MANAGER)
    if by.pk in (obj.created_by_id, obj.submitted_by_id):
        raise ValidationError("Quem elaborou ou enviou a revisão não a aprova nem a devolve.")


def return_revision(kind: str, obj, *, by, comment: str, request=None):
    adapter = get_adapter(kind)
    comment = (comment or "").strip()
    if not comment:
        raise ValidationError("Informe o comentário da devolução.")
    _require_decider(adapter, obj, by)
    with transaction.atomic():
        obj = adapter.lock(obj)
        if obj.status != "draft" or obj.review_status != ReviewStatus.SUBMITTED:
            raise ValidationError("Só revisão enviada para aprovação é devolvida.")
        obj.review_status = ReviewStatus.EDITING
        obj.save(update_fields=["review_status"])
        record_step(adapter, obj, Step.RETURNED, by, comment)
        _event(
            "templates.returned",
            obj,
            by,
            request=request,
            old_value={"situacao": "enviada"},
            new_value={"situacao": "rascunho"},
            reason=comment,
        )
    return obj


def _sign(adapter, obj, by, purpose, content_hash) -> TemplateSignature:
    return TemplateSignature.objects.create(
        kind=adapter.kind,
        template_id=obj.pk,
        version=adapter.version(obj),
        purpose=purpose,
        content_hash=content_hash,
        signer=by,
        signer_name=by.get_full_name() or by.username,
        signer_title=getattr(by, "job_title", "") or "",
    )


def approve(kind: str, obj, *, by, password: str, valid_from=None, request=None):
    """Aprovação com assinatura e vigência imediata ou futura; publica a versão (FR-009, FR-010)."""
    adapter = get_adapter(kind)
    obj = adapter.get(obj.pk)
    _require_decider(adapter, obj, by)
    if obj.status != "draft" or obj.review_status != ReviewStatus.SUBMITTED:
        raise ValidationError("Só revisão enviada para aprovação é aprovada.")
    today = timezone.localdate()
    valid_from = valid_from or today
    if valid_from < today:
        raise ValidationError("A vigência não pode ser anterior a hoje.")
    current = adapter.current(obj)
    if current and valid_from < current.valid_from:
        raise ValidationError(
            f"A vigência não pode ser anterior à da versão vigente ({current.valid_from:%d/%m/%Y})."
        )
    reauthenticate(request, by, password)
    with transaction.atomic():
        obj = adapter.lock(obj)
        if obj.status != "draft" or obj.review_status != ReviewStatus.SUBMITTED:
            raise ValidationError("Só revisão enviada para aprovação é aprovada.")
        problems = adapter.errors(obj)
        if problems:
            raise ValidationError(problems)
        obj.valid_from = valid_from
        content_hash = digest(adapter, obj)
        adapter.publish(obj, by=by, valid_from=valid_from)
        obj.approved_hash = content_hash
        obj.save(update_fields=["approved_hash"])
        _sign(adapter, obj, by, SignaturePurpose.APPROVAL, content_hash)
        record_step(adapter, obj, Step.APPROVED, by)
        _event(
            "templates.approved",
            obj,
            by,
            request=request,
            new_value={
                "versao": adapter.version(obj),
                "vigencia": valid_from,
                "resumo": content_hash,
            },
        )
        if valid_from <= today:
            _became_current(adapter, obj, by, previous=current)
    return obj


def _became_current(adapter, obj, by=None, previous=None) -> None:
    record_step(adapter, obj, Step.BECAME_CURRENT, by)
    record_event(
        "templates.became_current",
        actor=by,
        obj=obj,
        new_value={
            "versao": adapter.version(obj),
            "anterior": adapter.version(previous) if previous else None,
        },
    )


def discard(kind: str, obj, *, by, reason: str, request=None):
    adapter = get_adapter(kind)
    _require(by, Profile.QUALITY, NOT_QUALITY)
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError("Informe o motivo do descarte.")
    with transaction.atomic():
        obj = adapter.lock(obj)
        if obj.status != "draft":
            raise ValidationError("Só rascunho de revisão é descartado.")
        require_editing(obj)
        obj.status = "discarded"
        obj.discarded_by, obj.discarded_at, obj.discard_reason = by, timezone.now(), reason
        obj.save(update_fields=["status", "discarded_by", "discarded_at", "discard_reason"])
        record_step(adapter, obj, Step.DISCARDED, by, reason)
        _event(
            "templates.discarded",
            obj,
            by,
            request=request,
            new_value={"versao": adapter.version(obj)},
            reason=reason,
        )
    return obj


def verify(kind: str, obj, *, by, request=None) -> dict:
    """Recalcula o resumo da versão publicada e compara com o aprovado e a assinatura (FR-014)."""
    adapter = get_adapter(kind)
    if not ({Profile.QUALITY, Profile.RD_MANAGER} & active_profiles(by)):
        raise ValidationError("Só a Qualidade/AR e o Gestor de P&D verificam modelos.")
    obj = adapter.get(obj.pk)
    if obj.status != "published":
        raise ValidationError("Só versão publicada é verificada.")
    actual = digest(adapter, obj)
    problems = []
    if not obj.approved_hash:
        problems.append("Versão publicada antes da revisão controlada: não há resumo aprovado.")
    elif actual != obj.approved_hash:
        problems.append("O conteúdo mudou depois da aprovação (resumo divergente).")
    signature = TemplateSignature.objects.filter(
        kind=adapter.kind, template_id=obj.pk, purpose=SignaturePurpose.APPROVAL
    ).first()
    if signature and signature.content_hash != actual:
        problems.append("O resumo assinado na aprovação não confere com o conteúdo atual.")
    result = {"integro": not problems, "problemas": problems, "resumo": actual}
    _event("templates.verified", obj, by, request=request, new_value=result)
    return result


def record_due(today=None) -> int:
    """Tarefa diária: registra a entrada em vigência das versões com data futura (FR-017)."""
    today = today or timezone.localdate()
    count = 0
    for adapter in ADAPTERS.values():
        seen = set()
        for obj in adapter.model.objects.filter(status="published", valid_from__lte=today):
            family = adapter.family(obj)
            if family in seen:
                continue
            seen.add(family)
            current = adapter.current(obj, today)
            if current is None:
                continue
            steps = TemplateStep.objects.filter(kind=adapter.kind, template_id=current.pk)
            if (
                steps.filter(step=Step.APPROVED).exists()
                and not steps.filter(step=Step.BECAME_CURRENT).exists()
            ):
                _became_current(adapter, current)
                count += 1
    return count


# ------------------------------------------------------------------ consulta


def history(kind: str, obj) -> list[dict]:
    adapter = get_adapter(kind)
    current = adapter.current(obj)
    rows = []
    for version in adapter.versions(obj):
        usage = adapter.usage(version)
        rows.append(
            {
                "obj": version,
                "situation": situation(adapter, version, current),
                "label": SITUATIONS[situation(adapter, version, current)],
                "steps": TemplateStep.objects.filter(
                    kind=adapter.kind, template_id=version.pk
                ).select_related("actor"),
                "signatures": TemplateSignature.objects.filter(
                    kind=adapter.kind, template_id=version.pk
                ),
                "usage": usage[:50],
                "usage_count": len(usage),
            }
        )
    return rows


def pending_reviews():
    rows = []
    for adapter in ADAPTERS.values():
        for obj in adapter.model.objects.filter(status="draft").order_by("pk"):
            rows.append(
                {
                    "kind": adapter.kind.value,
                    "obj": obj,
                    "family": adapter.family_label(obj),
                    "situation": SITUATIONS[obj.review_status],
                    "edit_url": adapter.edit_url(obj),
                }
            )
    return rows


# ------------------------------------------------------------------ retirada de uso


def is_retired(subdocument_type) -> bool:
    decided = (
        TemplateRetirement.objects.filter(subdocument_type=subdocument_type)
        .exclude(status=RetirementStatus.REQUESTED)
        .order_by("-decided_at", "-pk")
        .first()
    )
    return bool(decided and decided.status == RetirementStatus.APPROVED)


def request_retirement(template, *, by, reason: str, request=None) -> TemplateRetirement:
    adapter = get_adapter(TemplateKind.FORM)
    _require(by, Profile.QUALITY, NOT_QUALITY)
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError("Informe o motivo da retirada de uso.")
    current = adapter.current(template)
    if current is None or current.pk != template.pk:
        raise ValidationError("A retirada é pedida a partir da versão vigente do modelo.")
    try:
        with transaction.atomic():
            retirement = TemplateRetirement.objects.create(
                subdocument_type=template.subdocument_type, reason=reason, requested_by=by
            )
    except IntegrityError as exc:
        raise ValidationError(
            "Já existe pedido de retirada em andamento para este modelo."
        ) from exc
    _event(
        "templates.retirement_requested",
        template,
        by,
        request=request,
        new_value={"tipo": template.subdocument_type.label},
        reason=reason,
    )
    return retirement


def _require_retirement_decider(retirement, by):
    _require(by, Profile.RD_MANAGER, NOT_MANAGER)
    if by.pk == retirement.requested_by_id:
        raise ValidationError("Quem pediu a retirada não a aprova nem a devolve.")
    if retirement.status != RetirementStatus.REQUESTED:
        raise ValidationError("Este pedido de retirada já foi decidido.")


def approve_retirement(retirement, *, by, password: str, request=None) -> TemplateRetirement:
    adapter = get_adapter(TemplateKind.FORM)
    _require_retirement_decider(retirement, by)
    template = adapter.current(_FamilyProxy(retirement.subdocument_type))
    reauthenticate(request, by, password)
    with transaction.atomic():
        retirement = TemplateRetirement.objects.select_for_update().get(pk=retirement.pk)
        _require_retirement_decider(retirement, by)
        content_hash = digest(adapter, template)
        signature = _sign(adapter, template, by, SignaturePurpose.RETIREMENT, content_hash)
        retirement.status = RetirementStatus.APPROVED
        retirement.decided_by, retirement.decided_at = by, timezone.now()
        retirement.signature = signature
        retirement.save(update_fields=["status", "decided_by", "decided_at", "signature"])
        _event(
            "templates.retirement_approved",
            template,
            by,
            request=request,
            new_value={"tipo": retirement.subdocument_type.label, "resumo": content_hash},
        )
    return retirement


def return_retirement(retirement, *, by, comment: str, request=None) -> TemplateRetirement:
    comment = (comment or "").strip()
    if not comment:
        raise ValidationError("Informe o comentário da devolução.")
    _require_retirement_decider(retirement, by)
    adapter = get_adapter(TemplateKind.FORM)
    template = adapter.current(_FamilyProxy(retirement.subdocument_type))
    with transaction.atomic():
        retirement.status = RetirementStatus.RETURNED
        retirement.decided_by, retirement.decided_at = by, timezone.now()
        retirement.comment = comment
        retirement.save(update_fields=["status", "decided_by", "decided_at", "comment"])
        if template is not None:
            _event("templates.retirement_returned", template, by, request=request, reason=comment)
    return retirement


class _FamilyProxy:
    """Objeto mínimo para consultar a vigente de um tipo de subdocumento."""

    def __init__(self, subdocument_type):
        self.subdocument_type = subdocument_type
