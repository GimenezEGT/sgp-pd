"""Criar, corrigir, bloquear e desativar cadastros (FR-002 a FR-006 da feature 003; research R1, R2).

- Versão não bloqueada: a correção altera a própria linha e a trilha guarda o valor anterior e o
  novo (`catalog.updated`).
- Versão bloqueada (usada em documento assinado): a correção exige motivo, a linha atual deixa de
  ser vigente e nasce a versão seguinte (`catalog.versioned`); a anterior fica intacta.
- O código de lote e de insumo não muda depois de qualquer bloqueio da linhagem.
- Correção sem mudança real não gera versão nem evento.
"""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from sgp.audit.services import record_event
from sgp.core.access import can_access_project
from sgp.core.diff import changed_fields
from sgp.projects.models import ProjectStatus

from .kinds import Kind, kind_for
from .models import Panel, PanelSample, Sample
from .permissions import can_edit_catalog

REASON_REQUIRED = (
    "Este cadastro já foi usado em documento assinado: a correção cria uma nova versão e exige "
    "o motivo."
)
FROZEN_CODE = "O código não pode mudar depois que o cadastro foi usado em documento assinado."
NOT_CURRENT = "Esta versão foi substituída; corrija a versão vigente."
STALE_MESSAGE = "Outra pessoa gravou este cadastro depois que você o abriu; recarregue a página."
NOT_EDITOR = "Seu perfil só consulta os cadastros."
STATUS_REASON = "Informe o motivo da mudança de situação."

UNCHANGED = "unchanged"
UPDATED = "updated"
VERSIONED = "versioned"


# ------------------------------------------------------------------ instantâneo


def _field_value(record, name: str):
    model_field = record._meta.get_field(name)
    value = getattr(record, name)
    if value is None:
        return None
    if model_field.choices:
        return getattr(record, f"get_{name}_display")()
    if not model_field.is_relation:
        return value
    if name == "certificate":
        return {"nome": value.original_name, "sha256": value.sha256}
    username = getattr(value, "username", None)
    if username:
        return username
    return str(value)


def sample_label(sample: Sample) -> str:
    return f"{sample.identifier} v{sample.version_display}"


def snapshot(record, kind: Kind | None = None, samples=None) -> dict:
    kind = kind or kind_for(record)
    data = {name: _field_value(record, name) for name in kind.fields}
    if kind.has_samples:
        if samples is None:
            samples = record.samples() if record.pk else []
        data["amostras"] = [sample_label(sample) for sample in samples]
    return data


def _event_payload(record, values: dict) -> dict:
    return {**values, "versao": record.version, "registro": record.pk}


def _record_event(event_type: str, record, by, kind: Kind, **kwargs):
    return record_event(
        event_type,
        actor=by,
        obj=record,
        object_id=str(record.lineage),
        project_id=getattr(record, "project_id", None),
        **kwargs,
    )


# --------------------------------------------------------------------- regras


def _check_editor(by, kind: Kind, data: dict) -> None:
    if not can_edit_catalog(by):
        raise ValidationError(NOT_EDITOR)
    if kind.project_scoped:
        project = data.get("project")
        if project is None or not can_access_project(by, project):
            raise ValidationError("Você não tem acesso ao projeto deste lote.")
        if project.status != ProjectStatus.OPEN:
            raise ValidationError("Lotes só podem ser cadastrados em projetos abertos.")


def _check_unique(kind: Kind, values: dict, lineage=None) -> None:
    if not kind.unique_together:
        return
    lookup = {name: values.get(name) for name in kind.unique_together}
    queryset = kind.model.objects.current().filter(**lookup)
    if lineage is not None:
        queryset = queryset.exclude(lineage=lineage)
    if queryset.exists():
        label = kind.model._meta.get_field(kind.unique_together[-1]).verbose_name
        raise ValidationError(
            f"Já existe {kind.label.lower()} vigente com {label} "
            f"{values.get(kind.unique_together[-1])}"
            + (" neste projeto." if kind.project_scoped else ".")
        )


def _check_samples(samples) -> list:
    samples = list(samples or [])
    lineages = [sample.lineage for sample in samples]
    if len(lineages) != len(set(lineages)):
        raise ValidationError("O painel não pode ter duas versões da mesma amostra.")
    return samples


def code_frozen(record) -> bool:
    return type(record).objects.filter(lineage=record.lineage, locked_at__isnull=False).exists()


def _save(record) -> None:
    try:
        with transaction.atomic():
            record.save()
    except IntegrityError as exc:
        raise ValidationError(
            "O cadastro conflita com outro vigente (código ou identificação repetida)."
        ) from exc


def _link_samples(panel: Panel, samples, by) -> None:
    PanelSample.objects.bulk_create(
        [
            PanelSample(panel=panel, sample=sample, position=position, added_by=by)
            for position, sample in enumerate(samples, start=1)
        ]
    )


def _relink_samples(panel: Panel, samples, by) -> None:
    now = timezone.now()
    wanted = {sample.pk: position for position, sample in enumerate(samples, start=1)}
    for link in panel.links.filter(removed_at__isnull=True).select_for_update():
        if link.sample_id in wanted:
            position = wanted.pop(link.sample_id)
            if link.position != position:
                link.position = position
                link.save(update_fields=["position"])
        else:
            link.removed_at = now
            link.removed_by = by
            link.save(update_fields=["removed_at", "removed_by"])
    by_pk = {sample.pk: sample for sample in samples}
    PanelSample.objects.bulk_create(
        [
            PanelSample(panel=panel, sample=by_pk[pk], position=position, added_by=by)
            for pk, position in wanted.items()
        ]
    )


# --------------------------------------------------------------------- serviços


def create_record(kind: Kind, *, by, data: dict, samples=None):
    """Cria a versão 1 do cadastro e grava `catalog.created` na mesma transação."""
    _check_editor(by, kind, data)
    samples = _check_samples(samples) if kind.has_samples else None
    with transaction.atomic():
        _check_unique(kind, data)
        record = kind.model(**data, created_by=by)
        _save(record)
        if kind.has_samples:
            _link_samples(record, samples, by)
        _record_event(
            "catalog.created",
            record,
            by,
            kind,
            new_value=_event_payload(record, snapshot(record, kind, samples)),
        )
    return record


def update_record(record, *, by, data: dict, reason: str = "", row_version=None, samples=None):
    """Corrige o cadastro; devolve (registro resultante, UNCHANGED | UPDATED | VERSIONED)."""
    kind = kind_for(record)
    model = type(record)
    reason = (reason or "").strip()
    with transaction.atomic():
        current = model.objects.select_for_update().get(pk=record.pk)
        if not current.is_current:
            raise ValidationError(NOT_CURRENT)
        if row_version is not None and int(row_version) != current.row_version:
            raise ValidationError(STALE_MESSAGE)
        _check_editor(by, kind, {**{name: getattr(current, name) for name in kind.fields}})
        if kind.has_samples:
            samples = _check_samples(samples if samples is not None else current.samples())
        if kind.project_scoped and "project" in data and data["project"] != current.project:
            raise ValidationError("O lote não muda de projeto; cadastre-o no projeto certo.")
        before = snapshot(current, kind)
        candidate = model.objects.get(pk=current.pk)
        for name, value in data.items():
            setattr(candidate, name, value)
        old, new = changed_fields(before, snapshot(candidate, kind, samples))
        if not new:
            return current, UNCHANGED
        if kind.code_field and kind.code_field in new and code_frozen(current):
            raise ValidationError(FROZEN_CODE)
        values = {name: getattr(candidate, name) for name in kind.fields}
        _check_unique(kind, values, lineage=current.lineage)
        now = timezone.now()
        if current.is_locked:
            if not reason:
                raise ValidationError(REASON_REQUIRED)
            current.is_current = False
            current.save(update_fields=["is_current"])
            successor = model(
                **values,
                lineage=current.lineage,
                version=current.version + 1,
                is_current=True,
                is_active=current.is_active,
                version_reason=reason,
                created_by=by,
                created_at=now,
            )
            _save(successor)
            if kind.has_samples:
                _link_samples(successor, samples, by)
            _record_event(
                "catalog.versioned",
                successor,
                by,
                kind,
                old_value=old,
                new_value=_event_payload(successor, new),
                reason=reason,
            )
            return successor, VERSIONED
        for name, value in values.items():
            setattr(current, name, value)
        current.row_version += 1
        current.updated_by = by
        current.updated_at = now
        _save(current)
        if kind.has_samples:
            _relink_samples(current, samples, by)
        _record_event(
            "catalog.updated",
            current,
            by,
            kind,
            old_value=old,
            new_value=_event_payload(current, new),
            reason=reason,
        )
        return current, UPDATED


def lock_version(record, *, by, reason: str):
    """Bloqueia a versão usada em documento assinado (chamado pela assinatura, feature 005).

    Bloquear um painel bloqueia também as versões das amostras dele. Versão já bloqueada não
    gera novo evento.
    """
    kind = kind_for(record)
    model = type(record)
    reason = (reason or "").strip() or "Usado em documento assinado"
    with transaction.atomic():
        row = model.objects.select_for_update().get(pk=record.pk)
        if row.locked_at is None:
            row.locked_at = timezone.now()
            row.locked_by = by
            row.lock_reason = reason[:300]
            row.save(update_fields=["locked_at", "locked_by", "lock_reason"])
            _record_event(
                "catalog.locked",
                row,
                by,
                kind,
                new_value={"versao": row.version, "registro": row.pk},
                reason=reason,
            )
        if kind.has_samples:
            for sample in row.samples():
                lock_version(sample, by=by, reason=f"{row}: {reason}")
    return row


def set_active(record, *, by, active: bool, reason: str):
    """Desativa ou reativa a versão vigente, com motivo (FR-006)."""
    kind = kind_for(record)
    model = type(record)
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError(STATUS_REASON)
    with transaction.atomic():
        row = model.objects.select_for_update().get(pk=record.pk)
        if not row.is_current:
            raise ValidationError(NOT_CURRENT)
        _check_editor(by, kind, {name: getattr(row, name) for name in kind.fields})
        if row.is_active == active:
            raise ValidationError(
                "O cadastro já está ativo." if active else "O cadastro já está desativado."
            )
        row.is_active = active
        row.row_version += 1
        row.updated_by = by
        row.updated_at = timezone.now()
        row.save(update_fields=["is_active", "row_version", "updated_by", "updated_at"])
        _record_event(
            "catalog.reactivated" if active else "catalog.deactivated",
            row,
            by,
            kind,
            old_value={"ativo": not active},
            new_value={"ativo": active, "versao": row.version, "registro": row.pk},
            reason=reason,
        )
    return row


def history(record):
    """Todas as versões do cadastro, da mais nova para a mais antiga (FR-005)."""
    return (
        type(record)
        .objects.filter(lineage=record.lineage)
        .select_related("created_by", "locked_by", "updated_by")
        .order_by("-version")
    )


def current_of(record):
    return type(record).objects.filter(lineage=record.lineage, is_current=True).first()
