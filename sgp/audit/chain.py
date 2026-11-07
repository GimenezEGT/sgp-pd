"""Serialização canônica e hash SHA-256 dos eventos (contrato eventos-auditoria.md).

O hash de cada evento cobre todos os campos exibidos e o hash do evento anterior; qualquer
alteração, inserção ou exclusão feita fora do sistema muda o resultado da verificação.
"""

import enum
import hashlib
import json
import uuid
from datetime import UTC, date, datetime, time
from decimal import Decimal
from pathlib import PurePath

GENESIS_HASH = "0" * 64
NUL = chr(0)
REPLACEMENT_CHARACTER = chr(0xFFFD)

HASH_FIELDS = (
    "seq",
    "occurred_at",
    "actor_id",
    "actor_username",
    "event_type",
    "object_type",
    "object_id",
    "object_repr",
    "project_id",
    "old_value",
    "new_value",
    "reason",
    "ip_address",
    "prev_hash",
)


def format_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("Data e hora do evento precisam ter fuso horário.")
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def _clean_text(value: str) -> str:
    # O PostgreSQL não aceita o caractere nulo em texto nem em JSONB.
    return value.replace(NUL, REPLACEMENT_CHARACTER)


def to_jsonable(value):
    """Reduz o valor a texto, inteiro, booleano, nulo, lista e objeto (sem ponto flutuante)."""
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return _clean_text(value)
    if isinstance(value, enum.Enum):
        return to_jsonable(value.value)
    if isinstance(value, float | Decimal):
        return format(value, "f") if isinstance(value, Decimal) else repr(value)
    if isinstance(value, datetime):
        return format_timestamp(value) if value.tzinfo else value.isoformat(timespec="microseconds")
    if isinstance(value, date | time):
        return value.isoformat()
    if isinstance(value, uuid.UUID | PurePath):
        return str(value)
    if isinstance(value, dict):
        return {_clean_text(str(key)): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [to_jsonable(item) for item in value]
    if isinstance(value, set | frozenset):
        items = [to_jsonable(item) for item in value]
        return sorted(items, key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))
    pk = getattr(value, "pk", None)
    if pk is not None:
        return to_jsonable(pk)
    return _clean_text(str(value))


def canonical_payload(fields: dict) -> bytes:
    data = {name: fields[name] for name in HASH_FIELDS}
    data["occurred_at"] = format_timestamp(data["occurred_at"])
    return json.dumps(
        data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def compute_hash(fields: dict) -> str:
    return hashlib.sha256(canonical_payload(fields)).hexdigest()
