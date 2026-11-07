"""Gravação e verificação da trilha de auditoria (FR-017 a FR-022 da feature 001)."""

import logging

from django.db import connection, transaction
from django.utils import timezone

from sgp.core.request_context import client_ip, current_request

from .chain import GENESIS_HASH, HASH_FIELDS, compute_hash, to_jsonable
from .event_types import EVENT_TYPES
from .models import AuditEvent, ChainVerification

logger = logging.getLogger(__name__)

# Chave da trava consultiva que serializa a gravação de eventos (cadeia única, sem lacunas).
ADVISORY_LOCK_KEY = 0x53475044  # "SGPD"
SYSTEM_ACTOR = "sistema"
ANONYMOUS = "anônimo"
REQUEST_USER = object()
VERIFY_CHUNK = 2000
MAX_BREAKS_STORED = 1000


def record_event(
    event_type: str,
    *,
    actor=REQUEST_USER,
    actor_username: str | None = None,
    obj=None,
    object_type: str = "",
    object_id: str = "",
    object_repr: str = "",
    project_id: int | None = None,
    old_value=None,
    new_value=None,
    reason: str = "",
    request=None,
) -> AuditEvent:
    """Grava um evento encadeado na transação corrente (evento e mudança juntos)."""
    if event_type not in EVENT_TYPES:
        raise ValueError(f"Tipo de evento não registrado no catálogo: {event_type}")
    request = request if request is not None else current_request()
    if actor is REQUEST_USER:
        user = getattr(request, "user", None)
        actor = user if user is not None and user.is_authenticated else None
    if obj is not None:
        object_type = object_type or f"{obj._meta.app_label}.{obj._meta.model_name}"
        object_id = object_id or str(obj.pk)
        object_repr = object_repr or str(obj)
    username = actor.username if actor is not None else (actor_username or SYSTEM_ACTOR)

    fields = {
        "actor_id": actor.pk if actor is not None else None,
        "actor_username": username[:150],
        "event_type": event_type,
        "object_type": (object_type or "")[:100],
        "object_id": str(object_id or "")[:64],
        "object_repr": (object_repr or "")[:255],
        "project_id": project_id,
        "old_value": to_jsonable(old_value),
        "new_value": to_jsonable(new_value),
        "reason": to_jsonable(reason or ""),
        "ip_address": client_ip(request),
    }
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [ADVISORY_LOCK_KEY])
        last = AuditEvent.objects.order_by("-seq").values_list("seq", "hash").first()
        seq, prev_hash = (last[0] + 1, last[1]) if last else (1, GENESIS_HASH)
        fields.update(seq=seq, occurred_at=timezone.now(), prev_hash=prev_hash)
        fields["hash"] = compute_hash(fields)
        return AuditEvent.objects.create(**fields)


def _break(seq, kind: str, detail: str) -> dict:
    return {"seq": seq, "kind": kind, "detail": detail}


def verify_chain(
    *, trigger: str = ChainVerification.Trigger.MANUAL, triggered_by=None
) -> ChainVerification:
    """Percorre toda a cadeia e registra o resultado (FR-021)."""
    started_at = timezone.now()
    breaks: list[dict] = []
    expected_seq = 1
    prev_hash = GENESIS_HASH
    count = 0
    head_seq, head_hash = None, ""
    rows = (
        AuditEvent.objects.order_by("seq")
        .values_list(*HASH_FIELDS, "hash")
        .iterator(chunk_size=VERIFY_CHUNK)
    )
    for row in rows:
        fields = dict(zip(HASH_FIELDS, row[:-1], strict=True))
        stored_hash = row[-1]
        seq = fields["seq"]
        count += 1
        if seq != expected_seq:
            breaks.append(
                _break(
                    seq, "sequence_gap", f"Esperado o evento {expected_seq}, encontrado o {seq}."
                )
            )
        if compute_hash(fields) != stored_hash:
            breaks.append(
                _break(seq, "content_altered", "O resumo recalculado não confere com o gravado.")
            )
        if fields["prev_hash"] != prev_hash:
            breaks.append(_break(seq, "chain_broken", "O resumo do evento anterior não confere."))
        prev_hash = stored_hash
        expected_seq = seq + 1
        head_seq, head_hash = seq, stored_hash

    checkpoint = (
        ChainVerification.objects.exclude(head_seq__isnull=True)
        .order_by("-finished_at", "-id")
        .first()
    )
    if checkpoint is not None:
        current = (
            AuditEvent.objects.filter(seq=checkpoint.head_seq)
            .values_list("hash", flat=True)
            .first()
        )
        if current is None:
            breaks.append(
                _break(
                    checkpoint.head_seq,
                    "checkpoint_missing",
                    "O último evento da verificação anterior não existe mais (trecho final apagado).",
                )
            )
        elif current != checkpoint.head_hash:
            breaks.append(
                _break(
                    checkpoint.head_seq,
                    "checkpoint_mismatch",
                    "O último evento da verificação anterior foi alterado.",
                )
            )

    status = ChainVerification.Status.BROKEN if breaks else ChainVerification.Status.INTACT
    with transaction.atomic():
        verification = ChainVerification.objects.create(
            started_at=started_at,
            finished_at=timezone.now(),
            trigger=trigger,
            triggered_by=triggered_by,
            events_checked=count,
            status=status,
            head_seq=head_seq,
            head_hash=head_hash,
            breaks=breaks[:MAX_BREAKS_STORED],
        )
        record_event(
            "audit.chain_verified",
            actor=triggered_by,
            obj=verification,
            new_value={
                "situacao": status,
                "eventos": count,
                "ultimo_seq": head_seq,
                "quebras": len(breaks),
            },
        )
    logger.info(
        "Verificação da trilha: situação=%s eventos=%s último=%s resumo=%s quebras=%s",
        status,
        count,
        head_seq,
        head_hash,
        len(breaks),
    )
    return verification


def latest_verification() -> ChainVerification | None:
    return ChainVerification.objects.order_by("-finished_at", "-id").first()


def integrity_alert_active() -> bool:
    latest = latest_verification()
    return latest is not None and latest.status == ChainVerification.Status.BROKEN
