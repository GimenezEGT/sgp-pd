"""Manutenção das listas controladas pela Qualidade/AR (FR-019 da feature 003; research R8).

Incluir termo, corrigir rótulo, desativar e reativar: nada é apagado, cada mudança sobe a
versão da lista e grava o evento `vocab.*` na mesma transação. Corrigir, desativar e reativar
exigem motivo.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils.text import slugify

from sgp.accounts.profiles import Profile, active_profiles
from sgp.audit.services import record_event

from .models import Term, Vocabulary

NOT_QUALITY = "Só a Qualidade/AR mantém as listas controladas."
REASON_REQUIRED = "Informe o motivo da mudança."


def _require_quality(by) -> None:
    if Profile.QUALITY not in active_profiles(by):
        raise ValidationError(NOT_QUALITY)


def _clean_label(label: str) -> str:
    label = " ".join((label or "").split())
    if not label:
        raise ValidationError("Informe o rótulo do termo.")
    if len(label) > 200:
        raise ValidationError("O rótulo pode ter até 200 caracteres.")
    return label


def _check_duplicate(vocabulary: Vocabulary, label: str, exclude_pk=None) -> None:
    queryset = vocabulary.terms.filter(label__iexact=label)
    if exclude_pk is not None:
        queryset = queryset.exclude(pk=exclude_pk)
    if queryset.exists():
        raise ValidationError(f"Já existe o termo {label!r} nesta lista.")


def _unique_code(vocabulary: Vocabulary, label: str) -> str:
    base = slugify(label)[:50] or "termo"
    code, suffix = base, 2
    while vocabulary.terms.filter(code=code).exists():
        code = f"{base}-{suffix}"
        suffix += 1
    return code


def _bump(vocabulary: Vocabulary) -> int:
    vocabulary.version += 1
    vocabulary.save(update_fields=["version"])
    return vocabulary.version


def _event(event_type: str, term: Term, by, **kwargs):
    return record_event(event_type, actor=by, obj=term, **kwargs)


def add_term(vocabulary: Vocabulary, *, by, label: str, reason: str = "") -> Term:
    _require_quality(by)
    label = _clean_label(label)
    with transaction.atomic():
        vocabulary = Vocabulary.objects.select_for_update().get(pk=vocabulary.pk)
        _check_duplicate(vocabulary, label)
        position = (vocabulary.terms.aggregate(top=Max("position"))["top"] or 0) + 1
        term = Term.objects.create(
            vocabulary=vocabulary,
            code=_unique_code(vocabulary, label),
            label=label,
            position=position,
        )
        version = _bump(vocabulary)
        _event(
            "vocab.term_created",
            term,
            by,
            new_value={"lista": vocabulary.code, "rotulo": label, "versao_lista": version},
            reason=(reason or "").strip(),
        )
    return term


def relabel_term(term: Term, *, by, label: str, reason: str) -> Term:
    _require_quality(by)
    label = _clean_label(label)
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError(REASON_REQUIRED)
    with transaction.atomic():
        vocabulary = Vocabulary.objects.select_for_update().get(pk=term.vocabulary_id)
        term = Term.objects.select_for_update().get(pk=term.pk)
        if term.label == label:
            raise ValidationError("O rótulo não mudou.")
        _check_duplicate(vocabulary, label, exclude_pk=term.pk)
        old_label = term.label
        term.label = label
        term.save(update_fields=["label"])
        version = _bump(vocabulary)
        _event(
            "vocab.term_updated",
            term,
            by,
            old_value={"rotulo": old_label},
            new_value={"lista": vocabulary.code, "rotulo": label, "versao_lista": version},
            reason=reason,
        )
    return term


def set_term_active(term: Term, *, by, active: bool, reason: str) -> Term:
    _require_quality(by)
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError(REASON_REQUIRED)
    with transaction.atomic():
        vocabulary = Vocabulary.objects.select_for_update().get(pk=term.vocabulary_id)
        term = Term.objects.select_for_update().get(pk=term.pk)
        if term.is_active == active:
            raise ValidationError(
                "O termo já está ativo." if active else "O termo já está desativado."
            )
        term.is_active = active
        term.save(update_fields=["is_active"])
        version = _bump(vocabulary)
        _event(
            "vocab.term_reactivated" if active else "vocab.term_deactivated",
            term,
            by,
            old_value={"ativo": not active},
            new_value={"lista": vocabulary.code, "ativo": active, "versao_lista": version},
            reason=reason,
        )
    return term
