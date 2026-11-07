"""Serialização canônica e hash dos eventos (FR-020; contrato eventos-auditoria.md)."""

import hashlib
import json
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from sgp.audit.chain import GENESIS_HASH, HASH_FIELDS, canonical_payload, compute_hash, to_jsonable

pytestmark = pytest.mark.req("001:FR-020")


def sample_fields(**overrides):
    fields = {
        "seq": 42,
        "occurred_at": datetime(2026, 11, 7, 13, 5, 22, 123456, tzinfo=UTC),
        "actor_id": 12,
        "actor_username": "ana.silva",
        "event_type": "accounts.profile_granted",
        "object_type": "accounts.profileassignment",
        "object_id": "7",
        "object_repr": "Analista/Pesquisador - ana.silva",
        "project_id": None,
        "old_value": {"perfis": []},
        "new_value": {"perfis": ["ANALYST"]},
        "reason": "Entrada no projeto",
        "ip_address": "10.0.0.15",
        "prev_hash": "a" * 64,
    }
    fields.update(overrides)
    return fields


def test_payload_canonico_tem_chaves_ordenadas_e_sem_espacos():
    payload = canonical_payload(sample_fields()).decode("utf-8")
    assert payload.startswith('{"actor_id":12,"actor_username":"ana.silva","event_type"')
    assert '"occurred_at":"2026-11-07T13:05:22.123456+00:00"' in payload
    assert ": " not in payload and ", " not in payload
    assert list(json.loads(payload)) == sorted(HASH_FIELDS)


def test_hash_e_sha256_do_payload():
    fields = sample_fields()
    expected = hashlib.sha256(canonical_payload(fields)).hexdigest()
    assert compute_hash(fields) == expected
    assert len(expected) == 64


def test_qualquer_campo_alterado_muda_o_hash():
    original = compute_hash(sample_fields())
    for name, value in [
        ("seq", 43),
        ("reason", "outro motivo"),
        ("new_value", {"perfis": ["READER"]}),
        ("prev_hash", "b" * 64),
        ("occurred_at", datetime(2026, 11, 7, 13, 5, 22, 123457, tzinfo=UTC)),
        ("ip_address", "10.0.0.16"),
    ]:
        assert compute_hash(sample_fields(**{name: value})) != original, name


def test_ordem_das_chaves_dos_valores_nao_muda_o_hash():
    first = compute_hash(sample_fields(new_value={"a": 1, "b": 2}))
    second = compute_hash(sample_fields(new_value={"b": 2, "a": 1}))
    assert first == second


def test_genesis_tem_64_zeros():
    assert GENESIS_HASH == "0" * 64


def test_data_sem_fuso_e_recusada():
    with pytest.raises(ValueError):
        canonical_payload(sample_fields(occurred_at=datetime(2026, 1, 1, 12, 0)))


def test_to_jsonable_reduz_tipos_sem_ponto_flutuante():
    value = to_jsonable(
        {
            "decimal": Decimal("10.50"),
            "float": 0.1,
            "data": date(2026, 11, 7),
            "momento": datetime(2026, 11, 7, 10, 0, tzinfo=UTC),
            "uuid": uuid.UUID("12345678-1234-5678-1234-567812345678"),
            "conjunto": {"b", "a"},
            "tupla": (1, 2),
            "texto": "nulo" + chr(0) + "aqui",
            "logico": True,
        }
    )
    assert value == {
        "decimal": "10.50",
        "float": "0.1",
        "data": "2026-11-07",
        "momento": "2026-11-07T10:00:00.000000+00:00",
        "uuid": "12345678-1234-5678-1234-567812345678",
        "conjunto": ["a", "b"],
        "tupla": [1, 2],
        "texto": "nulo" + chr(0xFFFD) + "aqui",
        "logico": True,
    }
