"""Criação, gravação, migração, autorização de fluxo e aprovação de subdocumentos (feature 004).

Toda mudança grava o evento na mesma transação. A aprovação é provisória (confirmação registrada
do Gestor de P&D que não criou o documento) até a feature 005; ela bloqueia o documento e as
versões dos cadastros que ele referencia.
"""

import copy

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from sgp.audit.services import record_event
from sgp.catalog.kinds import get_kind
from sgp.catalog.versioning import lock_version
from sgp.files.storage import check_upload, store_upload
from sgp.formtemplates import fieldtypes
from sgp.formtemplates.schema import DISPLAY_ONLY
from sgp.formtemplates.services import current_template

from . import derived, flow, numbering, permissions
from .models import (
    CHANGE,
    ENTRY,
    FINAL_CHECK,
    FlowAuthorization,
    FlowAuthorizationUse,
    Subdocument,
    SubdocumentStatus,
)

NOT_EDITOR = "Só membros da equipe (Analista ou Líder) e o Gestor de P&D editam subdocumentos de projeto aberto."
NOT_DRAFT = "O subdocumento está aprovado e não pode ser editado."
STALE = "Outra pessoa gravou este subdocumento depois que você o abriu; recarregue a página."


class FlowAuthorizationRequired(ValidationError):
    """Criação fora da ordem recomendada: falta a autorização do Gestor de P&D."""

    def __init__(self, requirement):
        super().__init__(
            f"Ordem do fluxo: falta {requirement.missing}. A criação só segue com autorização "
            "registrada do Gestor de P&D."
        )
        self.requirement = requirement


# ------------------------------------------------------------------- utilidades


def _event(event_type: str, subdocument: Subdocument, by, **kwargs):
    return record_event(
        event_type, actor=by, obj=subdocument, project_id=subdocument.project_id, **kwargs
    )


def _require_editor(by, project) -> None:
    if not permissions.can_edit(by, project):
        raise ValidationError(NOT_EDITOR)


def _require_draft(subdocument: Subdocument) -> None:
    if not subdocument.is_draft:
        raise ValidationError(NOT_DRAFT)


def entry_topics(project) -> tuple[list[str], dict]:
    entry = flow.approved(project, ENTRY)
    if entry is None:
        return [], {}
    keys = [topic["key"] for topic in entry.template.topics]
    labels = {topic["key"]: topic["label"] for topic in entry.template.topics}
    return keys, labels


def context_for(subdocument: Subdocument, by=None, previous=None) -> fieldtypes.Context:
    keys, labels = entry_topics(subdocument.project)
    return fieldtypes.Context(
        project=subdocument.project,
        subdocument=subdocument,
        by=by,
        previous=previous,
        entry_topic_keys=tuple(keys),
        entry_topic_labels=labels,
    )


def collect_files(template, data: dict) -> list[int]:
    found = []
    for topic in template.topics:
        values = data.get("topics", {}).get(topic["key"], {}).get("values", {})
        for field_def in topic.get("fields", []):
            for pk in fieldtypes.attachments(field_def, values.get(field_def["key"])):
                if pk not in found:
                    found.append(pk)
    return found


def _prefill(field_def: dict, project):
    source = field_def.get("prefill")
    if source == "project.product_name":
        return project.product_name
    if source == "project.title":
        return project.title
    if source == "project.classification_rule":
        return project.classification_rule or ""
    if source == "project.risk_class":
        return project.risk_class or ""
    return None


def initial_data(template, project) -> dict:
    """Dados iniciais: pré-preenchimento do projeto, tópicos herdados e linhas derivadas."""
    topics = {}
    for topic in template.topics:
        values = {}
        inherit = topic.get("inherit")
        if inherit:
            source = flow.approved(project, inherit["subdocument"])
            if source is not None:
                values = copy.deepcopy(source.topic_data(inherit["topic"])["values"])
        for field_def in topic.get("fields", []):
            if field_def["type"] == "derived_table":
                values[field_def["key"]] = derived.merge(
                    derived.build_rows(field_def, project), None
                )
            elif field_def.get("prefill"):
                values[field_def["key"]] = _prefill(field_def, project)
        topics[topic["key"]] = {"na": False, "justification": "", "values": values}
    return {"topics": topics, "files": []}


# --------------------------------------------------------------------- criação


def _authorization(project, subdocument_type):
    return (
        FlowAuthorization.objects.filter(project=project, subdocument_type=subdocument_type)
        .filter(use__isnull=True)
        .order_by("authorized_at")
        .first()
    )


def create_subdocument(project, subdocument_type, *, by) -> Subdocument:
    _require_editor(by, project)
    code = subdocument_type.code
    with transaction.atomic():
        existing = Subdocument.objects.select_for_update().filter(
            project=project, subdocument_type=subdocument_type
        )
        if code != CHANGE and existing.exists():
            raise ValidationError(f"Este projeto já tem {subdocument_type.label}.")
        needed = flow.requirement(project, code)
        authorization = None
        if needed is not None:
            if not needed.overridable:
                raise ValidationError(f"Crie e aprove primeiro: {needed.missing}.")
            authorization = _authorization(project, subdocument_type)
            if authorization is None:
                raise FlowAuthorizationRequired(needed)
        template = current_template(subdocument_type)
        if template is None:
            raise ValidationError(f"Não há modelo vigente para {subdocument_type.label}.")
        sequence = (
            (existing.aggregate(top=Max("sequence"))["top"] or 0) + 1 if code == CHANGE else 1
        )
        subdocument = Subdocument(
            project=project,
            subdocument_type=subdocument_type,
            sequence=sequence,
            template=template,
            data=initial_data(template, project),
            created_by=by,
        )
        if code == CHANGE:
            subdocument.changed_version = project.version
            subdocument.new_version = (project.version or 0) + 1
        subdocument.save()
        if authorization is not None:
            FlowAuthorizationUse.objects.create(
                authorization=authorization, subdocument=subdocument
            )
        _event(
            "subdocuments.created",
            subdocument,
            by,
            new_value={
                "tipo": subdocument_type.label,
                "numero": sequence,
                "modelo": template.version_display,
                "versao": subdocument.version_display,
                "autorizacao": authorization.pk if authorization else None,
            },
        )
    return subdocument


def authorize_flow(project, subdocument_type, *, by, reason: str) -> FlowAuthorization:
    if not permissions.is_manager(by) or not permissions.can_view(by, project):
        raise ValidationError("Só o Gestor de P&D autoriza a criação fora da ordem.")
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError("Informe o motivo da autorização.")
    needed = flow.requirement(project, subdocument_type.code)
    if needed is None:
        raise ValidationError("A ordem do fluxo já foi cumprida; não é preciso autorizar.")
    if not needed.overridable:
        raise ValidationError(f"{needed.missing} é obrigatória e não pode ser dispensada.")
    with transaction.atomic():
        authorization = FlowAuthorization.objects.create(
            project=project,
            subdocument_type=subdocument_type,
            missing_requirement=needed.missing,
            reason=reason,
            authorized_by=by,
        )
        record_event(
            "subdocuments.flow_authorized",
            actor=by,
            obj=authorization,
            project_id=project.pk,
            new_value={"tipo": subdocument_type.label, "falta": needed.missing},
            reason=reason,
        )
    return authorization


# --------------------------------------------------------------------- gravação


def validate_data(subdocument: Subdocument, data: dict) -> list[str]:
    """Formato e regras de "não aplicável" de cada tópico visível."""
    errors = []
    for number, topic in numbering.visible_topics(subdocument):
        name = f"Tópico {number} ({topic['label']})" if number else topic["label"]
        topic_data = data["topics"].get(topic["key"], {})
        values = topic_data.get("values", {})
        if topic_data.get("na"):
            if not topic.get("allow_not_applicable"):
                errors.append(f"{name}: este tópico não aceita 'não aplicável'.")
            if not topic_data.get("justification"):
                errors.append(f"{name}: 'não aplicável' exige justificativa.")
            filled = [
                fieldtypes.label_of(field_def)
                for field_def in topic.get("fields", [])
                if field_def["type"] not in DISPLAY_ONLY
                and field_def["type"] != "derived_table"
                and not fieldtypes.is_empty(field_def, values.get(field_def["key"]))
            ]
            if filled:
                errors.append(
                    f"{name}: marcado 'não aplicável' mas com campos preenchidos ({', '.join(filled)}); "
                    "limpe os campos ou desmarque 'não aplicável'."
                )
        previous = subdocument.topic_data(topic["key"])["values"]
        for field_def in topic.get("fields", []):
            if field_def["type"] in DISPLAY_ONLY:
                continue
            ctx = context_for(subdocument, previous=previous.get(field_def["key"]))
            errors.extend(
                f"{name} › {message}"
                for message in fieldtypes.validate(field_def, values.get(field_def["key"]), ctx)
            )
    return errors


def save_subdocument(subdocument: Subdocument, *, by, data: dict, uploads=(), row_version=None):
    """Grava o rascunho (pode ficar incompleto); recusa formato inválido e versão desatualizada."""
    with transaction.atomic():
        subdocument = (
            Subdocument.objects.select_for_update()
            .select_related("project", "template", "subdocument_type")
            .get(pk=subdocument.pk)
        )
        _require_editor(by, subdocument.project)
        _require_draft(subdocument)
        if row_version is not None and int(row_version) != subdocument.row_version:
            raise ValidationError(STALE)
        merged = copy.deepcopy(subdocument.data or {"topics": {}})
        merged.setdefault("topics", {})
        for key, topic_data in data.get("topics", {}).items():
            merged["topics"][key] = topic_data
        errors = validate_data(subdocument, merged)
        for _, _, files in uploads:
            for uploaded in files:
                try:
                    check_upload(uploaded)
                except ValidationError as exc:
                    errors.extend(f"{uploaded.name}: {message}" for message in exc.messages)
        if errors:
            raise ValidationError(errors)
        for topic_key, field_key, files in uploads:
            stored = [store_upload(uploaded, by=by).pk for uploaded in files]
            if stored:
                values = merged["topics"][topic_key]["values"]
                values[field_key] = list(values.get(field_key) or []) + stored
        merged["files"] = collect_files(subdocument.template, merged)
        before = (subdocument.data or {}).get("topics", {})
        after = merged["topics"]
        old = {key: before.get(key) for key in after if before.get(key) != after.get(key)}
        new = {key: after.get(key) for key in old}
        subdocument.data = merged
        subdocument.updated_by = by
        subdocument.updated_at = timezone.now()
        subdocument.row_version += 1
        subdocument.save()
        if new:
            _event("subdocuments.updated", subdocument, by, old_value=old, new_value=new)
    return subdocument


def refresh_derived(subdocument: Subdocument, *, by) -> Subdocument:
    """Recompõe as linhas derivadas da Entrada aprovada (e dos marcos), preservando o preenchido."""
    with transaction.atomic():
        subdocument = Subdocument.objects.select_for_update().get(pk=subdocument.pk)
        _require_editor(by, subdocument.project)
        _require_draft(subdocument)
        data = copy.deepcopy(subdocument.data)
        old, new = {}, {}
        for topic in subdocument.template.topics:
            values = data["topics"].setdefault(
                topic["key"], {"na": False, "justification": "", "values": {}}
            )["values"]
            for field_def in topic.get("fields", []):
                if field_def["type"] != "derived_table":
                    continue
                rows = derived.merge(
                    derived.build_rows(field_def, subdocument.project), values.get(field_def["key"])
                )
                if rows != values.get(field_def["key"]):
                    old[f"{topic['key']}.{field_def['key']}"] = values.get(field_def["key"])
                    new[f"{topic['key']}.{field_def['key']}"] = rows
                    values[field_def["key"]] = rows
        if new:
            subdocument.data = data
            subdocument.row_version += 1
            subdocument.updated_by = by
            subdocument.updated_at = timezone.now()
            subdocument.save()
            _event("subdocuments.derived_refreshed", subdocument, by, old_value=old, new_value=new)
    return subdocument


# -------------------------------------------------------------------- migração


def migrate_template(subdocument: Subdocument, *, by, reason: str) -> Subdocument:
    """Leva o rascunho para a versão vigente do modelo, guardando o que não couber (FR-007)."""
    reason = (reason or "").strip()
    if not permissions.is_manager(by):
        raise ValidationError("Só o Gestor de P&D migra documentos para outra versão de modelo.")
    if not reason:
        raise ValidationError("Informe o motivo da migração.")
    with transaction.atomic():
        subdocument = Subdocument.objects.select_for_update().get(pk=subdocument.pk)
        _require_draft(subdocument)
        target = current_template(subdocument.subdocument_type)
        if target is None or target.pk == subdocument.template_id:
            raise ValidationError("O documento já está na versão vigente do modelo.")
        old_topics = (subdocument.data or {}).get("topics", {})
        new_topics, unmapped = {}, {}
        target_keys = {topic["key"]: topic for topic in target.topics}
        source_defs = {topic["key"]: topic for topic in subdocument.template.topics}
        for key, topic_data in old_topics.items():
            target_topic = target_keys.get(key)
            if target_topic is None:
                if topic_data.get("values") or topic_data.get("na"):
                    unmapped[key] = topic_data
                continue
            target_fields = {
                field_def["key"]: field_def for field_def in target_topic.get("fields", [])
            }
            source_fields = {
                field_def["key"]: field_def
                for field_def in source_defs.get(key, {}).get("fields", [])
            }
            values = {}
            for field_key, value in topic_data.get("values", {}).items():
                target_field = target_fields.get(field_key)
                source_field = source_fields.get(field_key, {})
                if target_field and target_field["type"] == source_field.get(
                    "type", target_field["type"]
                ):
                    values[field_key] = value
                elif value not in (None, "", [], {}):
                    unmapped.setdefault(key, {"values": {}})["values"][field_key] = value
            new_topics[key] = {**topic_data, "values": values}
        initial = initial_data(target, subdocument.project)["topics"]
        for key, topic_data in initial.items():
            new_topics.setdefault(key, topic_data)
        previous_template = subdocument.template
        subdocument.template = target
        subdocument.data = {"topics": new_topics}
        subdocument.data["files"] = collect_files(target, subdocument.data)
        subdocument.unmapped_data = (
            {
                **(subdocument.unmapped_data or {}),
                previous_template.version_display: unmapped,
            }
            if unmapped
            else subdocument.unmapped_data
        )
        subdocument.row_version += 1
        subdocument.updated_by = by
        subdocument.updated_at = timezone.now()
        subdocument.save()
        _event(
            "subdocuments.template_migrated",
            subdocument,
            by,
            old_value={"modelo": previous_template.version_display},
            new_value={"modelo": target.version_display, "nao_migrados": unmapped},
            reason=reason,
        )
    return subdocument


# -------------------------------------------------------------------- aprovação


def completeness(subdocument: Subdocument) -> list[str]:
    """O que falta para aprovar: obrigatórios, 'não aplicável' justificado e regras do tópico."""
    missing = []
    for number, topic in numbering.visible_topics(subdocument):
        name = f"Tópico {number} ({topic['label']})" if number else topic["label"]
        topic_data = subdocument.topic_data(topic["key"])
        if topic_data["na"]:
            if not topic_data["justification"]:
                missing.append(f"{name}: 'não aplicável' exige justificativa.")
            continue
        values = topic_data["values"]
        for field_def in topic.get("fields", []):
            if field_def["type"] in DISPLAY_ONLY:
                continue
            missing.extend(
                f"{name} › {message}"
                for message in fieldtypes.incomplete(field_def, values.get(field_def["key"]))
            )
        any_of = topic.get("require_any")
        if any_of:
            fields = {field_def["key"]: field_def for field_def in topic.get("fields", [])}
            if all(
                fieldtypes.is_empty(fields[key], values.get(key)) for key in any_of if key in fields
            ):
                labels = [fieldtypes.label_of(fields[key]) for key in any_of if key in fields]
                missing.append(f"{name}: preencha {' ou '.join(labels)}.")
    if (
        subdocument.subdocument_type.code == FINAL_CHECK
        and flow.approved(subdocument.project, ENTRY) is None
    ):
        missing.append("A Entrada de Projeto precisa estar aprovada.")
    return missing


def _lock_references(subdocument: Subdocument, by) -> int:
    count = 0
    reason = (
        f"{subdocument} aprovado no projeto {subdocument.project.code or subdocument.project.pk}"
    )
    for topic in subdocument.template.topics:
        values = subdocument.topic_data(topic["key"])["values"]
        for field_def in topic.get("fields", []):
            for kind_slug, pk in fieldtypes.references(field_def, values.get(field_def["key"])):
                record = get_kind(kind_slug).model.objects.filter(pk=pk).first()
                if record is not None:
                    lock_version(record, by=by, reason=reason)
                    count += 1
    return count


def approve(subdocument: Subdocument, *, by) -> Subdocument:
    """Aprovação provisória (FR-015): Gestor de P&D ≠ criador; documento e cadastros bloqueados."""
    from sgp.projects.services import bump_version

    with transaction.atomic():
        subdocument = (
            Subdocument.objects.select_for_update()
            .select_related("project", "template", "subdocument_type")
            .get(pk=subdocument.pk)
        )
        if not permissions.is_manager(by):
            raise ValidationError("Só o Gestor de P&D aprova subdocumentos.")
        if subdocument.created_by_id == by.pk:
            raise ValidationError("Quem criou o subdocumento não pode aprová-lo.")
        _require_draft(subdocument)
        missing = completeness(subdocument)
        if missing:
            raise ValidationError(missing)
        subdocument.status = SubdocumentStatus.APPROVED
        subdocument.approved_by = by
        subdocument.approved_at = timezone.now()
        subdocument.save(update_fields=["status", "approved_by", "approved_at"])
        locked = _lock_references(subdocument, by)
        _event(
            "subdocuments.approved",
            subdocument,
            by,
            new_value={
                "versao": subdocument.version_display,
                "modelo": subdocument.template.version_display,
                "cadastros_bloqueados": locked,
            },
        )
        if subdocument.subdocument_type.code == CHANGE:
            _apply_change(subdocument, by, bump_version)
    return subdocument


def _apply_change(change: Subdocument, by, bump_version) -> None:
    """Alteração aprovada: versão do projeto sobe e os afetados ficam marcados para revisão."""
    bump_version(change.project, by=by, reason=f"{change} aprovada")
    affected = list(
        change.topic_data("subdocumentos_afetados")["values"].get("subdocumentos") or []
    )
    if change.topic_data("requisitos_entrada")["values"].get("afetados"):
        entry = flow.approved(change.project, ENTRY)
        if entry is not None and entry.pk not in affected:
            affected.append(entry.pk)
    now = timezone.now()
    for target in Subdocument.objects.filter(project=change.project, pk__in=affected).exclude(
        pk=change.pk
    ):
        target.review_requested_by = change
        target.review_requested_at = now
        target.save(update_fields=["review_requested_by", "review_requested_at"])
        _event("subdocuments.review_requested", target, by, new_value={"alteracao": str(change)})
