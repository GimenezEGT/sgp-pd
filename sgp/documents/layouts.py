"""Modelos de layout: vigência, rascunho, edição, publicação e vínculo por versão de documento.

Só a Qualidade/AR cria, altera, pré-visualiza e publica (FR-020). Publicado não muda (serviço e
gatilho no banco). Cada versão de documento usa o layout vigente quando começou (FR-021).
"""

import copy
import hashlib
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Max
from django.utils import timezone

from sgp.accounts.profiles import Profile, active_profiles
from sgp.audit.services import record_event
from sgp.core.diff import changed_fields
from sgp.files.storage import read_verified, store_upload

from . import layout_schema
from .models import LayoutBinding, LayoutStatus, LayoutTarget, LayoutTemplate

NOT_QUALITY = "Só a Qualidade/AR cria, altera, pré-visualiza e publica modelos de layout."
NOT_DRAFT = "Modelo de layout publicado não muda; crie uma nova versão."
STALE = "Outra pessoa gravou este rascunho depois que você o abriu; recarregue a página."
DEFAULT_LOGO = Path(__file__).resolve().parent / "static" / "documents" / "logo-bioclin-quibasa.png"
DEFAULT_LOGO_SHA256 = "766852392a3f6104c92d577733ec56fd1d1729bfb39a8da48d72d54fde7a1cea"
LOGO_KINDS = ("png", "jpeg")


class LogoIntegrityError(Exception):
    """A faixa padrão do logotipo não confere com o resumo registrado."""


def require_quality(by) -> None:
    if Profile.QUALITY not in active_profiles(by):
        raise ValidationError(NOT_QUALITY)


def current_layout(target: str, on=None) -> LayoutTemplate | None:
    """Versão vigente do alvo na data (publicada mais recente com vigência iniciada)."""
    on = on or timezone.localdate()
    return (
        LayoutTemplate.objects.filter(
            target=target, status=LayoutStatus.PUBLISHED, valid_from__lte=on
        )
        .order_by("-valid_from", "-version")
        .first()
    )


def first_layout(target: str) -> LayoutTemplate | None:
    return (
        LayoutTemplate.objects.filter(target=target, status=LayoutStatus.PUBLISHED)
        .order_by("version")
        .first()
    )


def _bind(kind: str, object_id: int, version: int, layout: LayoutTemplate) -> LayoutBinding:
    try:
        with transaction.atomic():
            return LayoutBinding.objects.create(
                kind=kind, object_id=object_id, version=version, layout=layout
            )
    except IntegrityError:
        return LayoutBinding.objects.get(kind=kind, object_id=object_id, version=version)


def bind_current(kind: str, object_id: int, version: int) -> LayoutBinding | None:
    """Chamado quando uma versão de documento começa (criação ou nova versão)."""
    existing = LayoutBinding.objects.filter(kind=kind, object_id=object_id, version=version).first()
    if existing:
        return existing
    layout = current_layout(kind) or first_layout(kind)
    return _bind(kind, object_id, version, layout) if layout else None


def layout_for(kind: str, object_id: int, version: int) -> LayoutTemplate:
    """Layout da versão do documento; versão sem vínculo (anterior à 006) usa a primeira publicada."""
    binding = (
        LayoutBinding.objects.select_related("layout")
        .filter(kind=kind, object_id=object_id, version=version)
        .first()
    )
    if binding:
        return binding.layout
    layout = first_layout(kind)
    if layout is None:
        raise ValidationError("Não há modelo de layout publicado para este tipo de documento.")
    return _bind(kind, object_id, version, layout).layout


def type_codes() -> list[str]:
    from sgp.vocab.models import Term

    return list(
        Term.objects.filter(vocabulary__code="tipo-subdocumento", is_active=True).values_list(
            "code", flat=True
        )
    )


def definition_errors(layout: LayoutTemplate, definition) -> list[str]:
    return layout_schema.validate_definition(
        definition, target=layout.target, type_codes=type_codes()
    )


def logo_bytes(layout: LayoutTemplate) -> bytes:
    """Logotipo da versão: o enviado (conferido pelo resumo) ou a faixa padrão da planilha."""
    if layout.logo_id:
        return read_verified(layout.logo)
    data = DEFAULT_LOGO.read_bytes()
    if hashlib.sha256(data).hexdigest() != DEFAULT_LOGO_SHA256:
        raise LogoIntegrityError("A faixa padrão do logotipo foi alterada fora do sistema.")
    return data


def _snapshot(layout: LayoutTemplate) -> dict:
    data = {"vigencia": layout.valid_from, "logotipo": layout.logo_id or "padrão"}
    for section, values in (layout.definition or {}).items():
        data[section] = values
    return data


def create_draft(target: str, *, by, source: LayoutTemplate | None = None) -> LayoutTemplate:
    require_quality(by)
    if target not in LayoutTarget.values:
        raise ValidationError("Alvo de layout inexistente.")
    with transaction.atomic():
        if LayoutTemplate.objects.filter(target=target, status=LayoutStatus.DRAFT).exists():
            raise ValidationError("Já existe um rascunho deste modelo de layout; continue nele.")
        source = source or current_layout(target) or first_layout(target)
        top = LayoutTemplate.objects.filter(target=target).aggregate(top=Max("version"))["top"]
        try:
            layout = LayoutTemplate.objects.create(
                target=target,
                version=(top or 0) + 1,
                valid_from=timezone.localdate(),
                definition=copy.deepcopy(source.definition)
                if source
                else layout_schema.default_definition(target),
                logo=source.logo if source else None,
                created_by=by,
            )
        except IntegrityError as exc:
            raise ValidationError(
                "Já existe um rascunho deste modelo de layout; continue nele."
            ) from exc
        record_event(
            "layouts.draft_created",
            actor=by,
            obj=layout,
            new_value={
                "alvo": layout.get_target_display(),
                "versao": layout.version_display,
                "a_partir_de": source.version_display if source else None,
            },
        )
    return layout


def update_draft(
    layout: LayoutTemplate,
    *,
    by,
    definition,
    valid_from=None,
    logo_upload=None,
    row_version=None,
) -> LayoutTemplate:
    require_quality(by)
    with transaction.atomic():
        layout = LayoutTemplate.objects.select_for_update().get(pk=layout.pk)
        if layout.status != LayoutStatus.DRAFT:
            raise ValidationError(NOT_DRAFT)
        if row_version is not None and int(row_version) != layout.row_version:
            raise ValidationError(STALE)
        errors = layout_schema.schema_errors(definition)
        if errors:
            raise ValidationError(errors)
        before = _snapshot(layout)
        if logo_upload is not None:
            layout.logo = store_upload(logo_upload, by=by, allowed=LOGO_KINDS)
        layout.definition = definition
        if valid_from is not None:
            layout.valid_from = valid_from
        layout.updated_by = by
        layout.updated_at = timezone.now()
        layout.row_version += 1
        layout.save()
        old, new = changed_fields(before, _snapshot(layout))
        if new:
            record_event(
                "layouts.draft_updated", actor=by, obj=layout, old_value=old, new_value=new
            )
    return layout


def publish(layout: LayoutTemplate, *, by, note: str = "") -> LayoutTemplate:
    require_quality(by)
    with transaction.atomic():
        layout = LayoutTemplate.objects.select_for_update().get(pk=layout.pk)
        if layout.status != LayoutStatus.DRAFT:
            raise ValidationError(NOT_DRAFT)
        errors = definition_errors(layout, layout.definition)
        current = current_layout(layout.target)
        if current and layout.valid_from < current.valid_from:
            errors.append(
                "A vigência não pode ser anterior à da versão vigente "
                f"({current.valid_from:%d/%m/%Y})."
            )
        if errors:
            raise ValidationError(errors)
        logo_bytes(layout)  # logotipo legível e íntegro antes de publicar
        layout.status = LayoutStatus.PUBLISHED
        layout.published_by = by
        layout.published_at = timezone.now()
        layout.note = note[:200]
        layout.save(update_fields=["status", "published_by", "published_at", "note"])
        record_event(
            "layouts.published",
            actor=by,
            obj=layout,
            new_value={
                "alvo": layout.get_target_display(),
                "versao": layout.version_display,
                "vigencia": layout.valid_from,
            },
        )
    return layout
