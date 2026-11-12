"""Outbox, envio com novas tentativas, reprocessamento, consulta de produto, mapeamento e
exportação de contingência (feature 012). Falha de integração nunca bloqueia o trabalho."""

import csv
import io
import json
import logging
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Max, Q
from django.utils import timezone
from openpyxl import Workbook

from sgp.accounts.profiles import Profile, active_profiles
from sgp.audit.services import record_event

from . import mapping, payloads, records, sankhya
from .models import IntegrationMapping, IntegrationMessage, MessageStatus

logger = logging.getLogger(__name__)
FORMATS = {
    "csv": "text/csv; charset=utf-8",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "json": "application/json",
}


def is_it(user) -> bool:
    return Profile.ADMIN in active_profiles(user)


def _require_it(user) -> None:
    if not is_it(user):
        raise PermissionDenied("Só a TI (Administrador do sistema) cuida da integração.")


def max_attempts() -> int:
    return int(getattr(settings, "INTEGRATION_MAX_ATTEMPTS", 6))


# ------------------------------------------------------------------ mapeamento


def current_mapping() -> IntegrationMapping:
    current = IntegrationMapping.objects.order_by("-version").first()
    if current is None:
        raise ValidationError("Não há mapeamento do Sankhya publicado.")
    return current


def publish_mapping(*, by, text: str, note: str = "") -> IntegrationMapping:
    _require_it(by)
    parsed = mapping.parse(text)
    with transaction.atomic():
        number = (IntegrationMapping.objects.aggregate(top=Max("version"))["top"] or 0) + 1
        record = IntegrationMapping.objects.create(
            version=number, yaml=text, parsed=parsed, note=note[:500], created_by=by
        )
        record_event(
            "integration.mapping_published",
            actor=by,
            obj=record,
            new_value={
                "versao": number,
                "registros_configurados": [
                    name for name, spec in parsed["registros"].items() if spec["entidade"]
                ],
            },
            reason=note[:500],
        )
    return record


# ------------------------------------------------------------------ outbox


def enqueue(
    record_type: str, key: str, payload: dict, *, project=None, obj=None
) -> IntegrationMessage | None:
    """Cria a mensagem na transação corrente (uma por chave) e agenda o envio depois do commit."""
    if IntegrationMessage.objects.filter(idempotency_key=key).exists():
        return None
    try:
        with transaction.atomic():
            message = IntegrationMessage.objects.create(
                record_type=record_type,
                idempotency_key=key,
                project=project,
                object_type=f"{obj._meta.app_label}.{obj._meta.model_name}"
                if obj is not None
                else "",
                object_id=str(obj.pk) if obj is not None else "",
                object_repr=str(obj)[:255] if obj is not None else "",
                payload=json.loads(json.dumps(payload, default=str)),
            )
    except IntegrityError:
        return None
    from .tasks import dispatch as dispatch_task

    transaction.on_commit(lambda: dispatch_task.delay(message.pk))
    return message


def _ready(record_type: str) -> tuple[dict | None, IntegrationMapping | None]:
    if not sankhya.configured():
        return None, None
    current = IntegrationMapping.objects.order_by("-version").first()
    if current is None:
        return None, None
    spec = current.parsed["registros"].get(record_type) or {}
    if not spec.get("entidade") or not spec.get("chave"):
        return None, current
    return spec, current


def dispatch(message_id: int) -> IntegrationMessage:
    """Envia por `saveRecord` com a chave de idempotência; erro agenda nova tentativa."""
    message = IntegrationMessage.objects.get(pk=message_id)
    if message.status == MessageStatus.SENT:
        return message
    spec, current = _ready(message.record_type)
    if spec is None:
        if message.status != MessageStatus.WAITING_CONFIG:
            IntegrationMessage.objects.filter(pk=message.pk).update(
                status=MessageStatus.WAITING_CONFIG
            )
            message.status = MessageStatus.WAITING_CONFIG
        return message
    fields = {
        target: message.payload.get(logical) for logical, target in spec["campos"].items() if target
    }
    body = payloads.save_record(spec["entidade"], spec["chave"], message.idempotency_key, fields)
    attempts = message.attempts + 1
    try:
        sankhya.call(body)
    except sankhya.SankhyaError as exc:
        error_text = str(exc)[:500]
        retry = attempts < max_attempts()
        next_at = timezone.now() + timedelta(minutes=2 ** (attempts - 1)) if retry else None
        with transaction.atomic():
            IntegrationMessage.objects.filter(pk=message.pk).update(
                status=MessageStatus.ERROR,
                attempts=attempts,
                last_error=error_text,
                next_attempt_at=next_at,
                mapping_version=current.version,
            )
            record_event(
                "integration.failed",
                actor=None,
                obj=message,
                project_id=message.project_id,
                new_value={
                    "chave": message.idempotency_key,
                    "tentativas": attempts,
                    "proxima": next_at,
                },
                reason=error_text,
            )
        message.refresh_from_db()
        return message
    with transaction.atomic():
        IntegrationMessage.objects.filter(pk=message.pk).update(
            status=MessageStatus.SENT,
            attempts=attempts,
            last_error="",
            next_attempt_at=None,
            sent_at=timezone.now(),
            mapping_version=current.version,
        )
        record_event(
            "integration.sent",
            actor=None,
            obj=message,
            project_id=message.project_id,
            new_value={
                "chave": message.idempotency_key,
                "entidade": spec["entidade"],
                "tentativas": attempts,
                "mapeamento": current.version,
            },
        )
    message.refresh_from_db()
    return message


def process_due(now=None) -> int:
    """Varredura do beat: mensagens na fila, com erro vencido ou aguardando configuração."""
    now = now or timezone.now()
    due = IntegrationMessage.objects.filter(
        Q(status=MessageStatus.PENDING)
        | Q(status=MessageStatus.WAITING_CONFIG)
        | Q(status=MessageStatus.ERROR, next_attempt_at__lte=now, attempts__lt=max_attempts())
    ).order_by("created_at")
    count = 0
    for message in due[:200]:
        dispatch(message.pk)
        count += 1
    return count


def reprocess(message: IntegrationMessage, *, by) -> IntegrationMessage:
    _require_it(by)
    if message.status == MessageStatus.SENT:
        raise ValidationError("A mensagem já foi enviada.")
    with transaction.atomic():
        IntegrationMessage.objects.filter(pk=message.pk).update(
            status=MessageStatus.PENDING, next_attempt_at=None
        )
        record_event(
            "integration.reprocessed",
            actor=by,
            obj=message,
            project_id=message.project_id,
            new_value={"chave": message.idempotency_key, "tentativas": message.attempts},
        )
    return dispatch(message.pk)


# ------------------------------------------------------------------ consulta de produto


class ProductNotFound(Exception):
    pass


def lookup_product(code: str) -> dict:
    code = (code or "").strip()
    if not code:
        raise ValidationError("Informe o código do produto.")
    current = IntegrationMapping.objects.order_by("-version").first()
    spec = (current.parsed["produto"] if current else {}) or {}
    if not sankhya.configured() or not spec.get("entidade"):
        raise sankhya.SankhyaUnavailable(
            "Integração com o Sankhya desligada ou sem mapeamento de produtos."
        )
    fields = spec["campos"]
    names = [fields[name] for name in mapping.PRODUCT_FIELDS if fields.get(name)]
    response = sankhya.call(payloads.load_records(spec["entidade"], names, fields["codigo"], code))
    found = payloads.rows(response)
    if not found:
        raise ProductNotFound(code)
    row = found[0]
    return {
        name: row.get(fields[name], "") if fields.get(name) else ""
        for name in mapping.PRODUCT_FIELDS
    }


# ------------------------------------------------------------------ contingência


def _br(value) -> str:
    if isinstance(value, float):
        return str(value).replace(".", ",")
    return "" if value is None else str(value)


def export(record_type: str, fmt: str, *, by, request=None) -> tuple[str, str, bytes]:
    _require_it(by)
    if record_type not in mapping.RECORD_FIELDS or fmt not in FORMATS:
        raise ValidationError("Escolha um registro e um formato (csv, xlsx ou json).")
    fields = list(mapping.RECORD_FIELDS[record_type])
    messages = IntegrationMessage.objects.filter(record_type=record_type).order_by(
        "created_at", "pk"
    )
    rows = [
        {"chave": m.idempotency_key, **{f: m.payload.get(f, "") for f in fields}} for m in messages
    ]
    columns = ["chave", *fields]
    stamp = timezone.localtime().strftime("%Y%m%d-%H%M%S")
    name = f"sgp-pd-{record_type}-{stamp}.{fmt}"
    if fmt == "csv":
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=";", lineterminator="\n")
        writer.writerow(columns)
        for row in rows:
            writer.writerow([_br(row[c]) for c in columns])
        data = buffer.getvalue().encode("utf-8")
    elif fmt == "xlsx":
        book = Workbook()
        sheet = book.active
        sheet.title = mapping.RECORD_LABELS[record_type][:31]
        sheet.append(columns)
        for row in rows:
            sheet.append([row[c] for c in columns])
        buffer = io.BytesIO()
        book.save(buffer)
        data = buffer.getvalue()
    else:
        envelope = {
            "entidade": record_type,
            "gerado_em": timezone.localtime().isoformat(),
            "registros": rows,
        }
        data = json.dumps(envelope, ensure_ascii=False, indent=2, default=str).encode("utf-8")
    record_event(
        "integration.exported",
        actor=by,
        object_type="integrations.export",
        object_id=record_type,
        object_repr=name,
        new_value={"registro": record_type, "formato": fmt, "linhas": len(rows)},
        request=request,
    )
    return name, FORMATS[fmt], data


# ------------------------------------------------------------------ geração pelas aprovações


def from_event(event) -> None:
    """Eventos da trilha que geram mensagens (contrato registros.md)."""
    from sgp.catalog.models import Lot, Material
    from sgp.projects.models import Project
    from sgp.studies.models import Study
    from sgp.subdocuments.models import Subdocument

    if event.event_type == "projects.approved" and event.object_type == "projects.project":
        project = (
            Project.objects.select_related("leader", "technology")
            .filter(pk=event.object_id)
            .first()
        )
        if project:
            kind, key, payload = records.project(project)
            enqueue(kind, key, payload, project=project, obj=project)
        return
    if event.event_type == "studies.locked":
        study = (
            Study.objects.select_related("project", "study_type", "subdocument")
            .filter(pk=event.object_id)
            .first()
        )
        if study:
            kind, key, payload = records.study_result(study)
            enqueue(kind, key, payload, project=study.project, obj=study)
        return
    if event.event_type != "signatures.approved" or event.object_type != "signatures.subdocument":
        return
    sub = (
        Subdocument.objects.select_related("project", "subdocument_type", "template")
        .filter(pk=event.object_id)
        .first()
    )
    if sub is None:
        return
    approval = _latest_approval(sub)
    if approval is None:
        return
    kind, key, payload = records.document(sub, approval)
    enqueue(kind, key, payload, project=sub.project, obj=sub)
    for lot in Lot.objects.select_related("project", "production_responsible").filter(
        pk__in=records.references(sub, approval, "lotes")
    ):
        kind, key, payload = records.lot(lot)
        enqueue(kind, key, payload, project=sub.project, obj=lot)
    if sub.subdocument_type.code == "saida":
        material_ids = records.references(
            sub,
            approval,
            "insumos",
            topic_keys={"novas_materias_primas", "novos_materiais_embalagem"},
        )
        for material in Material.objects.select_related("certificate").filter(pk__in=material_ids):
            kind, key, payload = records.new_material(material, sub.project)
            enqueue(kind, key, payload, project=sub.project, obj=material)


def _latest_approval(sub):
    from sgp.signatures.models import ApprovedVersion

    return (
        ApprovedVersion.objects.filter(kind="subdocument", object_id=sub.pk)
        .order_by("-version")
        .first()
    )
