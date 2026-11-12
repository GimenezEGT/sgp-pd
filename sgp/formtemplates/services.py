"""Rascunho e edição de modelos de formulário (FR-001 a FR-007 da feature 004).

Só a Qualidade/AR cadastra; a publicação é efeito da aprovação assinada da revisão (feature
013). Modelo publicado não muda: nova versão nasce como rascunho
com o conteúdo da vigente. A vigente de um tipo é a publicada mais recente já em vigência.
"""

import copy

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Max
from django.utils import timezone

from sgp.accounts.profiles import Profile, active_profiles
from sgp.audit.services import record_event
from sgp.core.diff import changed_fields
from sgp.vocab.models import Vocabulary

from . import schema
from .models import FormTemplate, TemplateStatus

NOT_QUALITY = "Só a Qualidade/AR cadastra e publica modelos de formulário."
NOT_DRAFT = "Modelo publicado não muda; crie uma nova versão."
STALE = "Outra pessoa gravou este rascunho depois que você o abriu; recarregue a página."
ENTRY = "entrada"


def _require_quality(by) -> None:
    if Profile.QUALITY not in active_profiles(by):
        raise ValidationError(NOT_QUALITY)


def current_template(subdocument_type, on=None) -> FormTemplate | None:
    """Versão vigente do tipo na data (publicada mais recente com vigência iniciada)."""
    from sgp.revisions.services import is_retired

    on = on or timezone.localdate()
    if is_retired(subdocument_type):  # feature 013: modelo retirado de uso não serve a novos
        return None
    return (
        FormTemplate.objects.filter(
            subdocument_type=subdocument_type, status=TemplateStatus.PUBLISHED, valid_from__lte=on
        )
        .order_by("-valid_from", "-form_version")
        .first()
    )


def entry_topic_keys(on=None) -> list[str] | None:
    from sgp.vocab.models import get_term

    entry = current_template(get_term("tipo-subdocumento", ENTRY), on)
    return [topic["key"] for topic in entry.topics] if entry else None


def definition_errors(template: FormTemplate, definition) -> list[str]:
    vocabularies = set(Vocabulary.objects.values_list("code", flat=True))
    keys = None if template.subdocument_type.code == ENTRY else entry_topic_keys()
    return schema.validate_definition(definition, vocabularies=vocabularies, entry_topic_keys=keys)


def _snapshot(template: FormTemplate) -> dict:
    return {
        "reference": template.reference,
        "valid_from": template.valid_from,
        **{f"topico:{topic['key']}": topic for topic in template.topics},
        "capa": template.cover,
    }


def create_draft(subdocument_type, *, by, source: FormTemplate | None = None) -> FormTemplate:
    from sgp.revisions import services as revisions

    _require_quality(by)
    family = FormTemplate.objects.filter(subdocument_type=subdocument_type).first()
    if family is not None:
        revisions.ensure_can_open("form", family)
    with transaction.atomic():
        if FormTemplate.objects.filter(
            subdocument_type=subdocument_type, status=TemplateStatus.DRAFT
        ).exists():
            raise ValidationError("Já existe um rascunho deste modelo; continue nele.")
        source = (
            source
            or current_template(subdocument_type)
            or (
                FormTemplate.objects.filter(subdocument_type=subdocument_type)
                .order_by("-form_version")
                .first()
            )
        )
        top = FormTemplate.objects.filter(subdocument_type=subdocument_type).aggregate(
            top=Max("form_version")
        )["top"]
        try:
            template = FormTemplate.objects.create(
                subdocument_type=subdocument_type,
                form_version=(top or 0) + 1,
                reference=source.reference if source else "",
                valid_from=timezone.localdate(),
                definition=copy.deepcopy(source.definition)
                if source
                else {"cover": {"title": subdocument_type.label}, "topics": []},
                created_by=by,
            )
        except IntegrityError as exc:
            raise ValidationError("Já existe um rascunho deste modelo; continue nele.") from exc
        revisions.opened("form", template, by)
        record_event(
            "formtemplates.draft_created",
            actor=by,
            obj=template,
            new_value={
                "tipo": subdocument_type.label,
                "versao": template.version_display,
                "a_partir_de": source.version_display if source else None,
            },
        )
    return template


def update_draft(template: FormTemplate, *, by, data: dict, definition, row_version=None):
    _require_quality(by)
    with transaction.atomic():
        template = FormTemplate.objects.select_for_update().get(pk=template.pk)
        if template.status != TemplateStatus.DRAFT:
            raise ValidationError(NOT_DRAFT)
        from sgp.revisions.services import require_editing

        require_editing(template)
        if row_version is not None and int(row_version) != template.row_version:
            raise ValidationError(STALE)
        errors = schema.schema_errors(definition)
        if errors:
            raise ValidationError(errors)
        before = _snapshot(template)
        template.reference = data.get("reference", template.reference)
        template.valid_from = data.get("valid_from", template.valid_from)
        template.definition = definition
        template.updated_by = by
        template.updated_at = timezone.now()
        template.row_version += 1
        template.save()
        old, new = changed_fields(before, _snapshot(template))
        if new:
            record_event(
                "formtemplates.draft_updated", actor=by, obj=template, old_value=old, new_value=new
            )
    return template
