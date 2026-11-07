"""Medições de desempenho (marcador slow): base para SC-005 e SC-007.

Rodar com: docker compose run --rm web pytest -m slow -s tests/audit/test_performance.py
"""

import time
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from sgp.accounts.profiles import Profile
from sgp.audit.chain import GENESIS_HASH, compute_hash
from sgp.audit.models import AuditEvent, ChainVerification
from sgp.audit.services import verify_chain

pytestmark = [pytest.mark.slow, pytest.mark.django_db]

TOTAL = 200_000


def bulk_chain(total: int, actor=None) -> None:
    start = timezone.now() - timedelta(days=60)
    prev = GENESIS_HASH
    batch = []
    for seq in range(1, total + 1):
        fields = {
            "seq": seq,
            "occurred_at": start + timedelta(seconds=seq * 20),
            "actor_id": actor.pk if actor and seq % 3 == 0 else None,
            "actor_username": actor.username if actor and seq % 3 == 0 else "sistema",
            "event_type": "audit.exported" if seq % 2 else "accounts.user_updated",
            "object_type": "",
            "object_id": "",
            "object_repr": "",
            "project_id": seq % 50,
            "old_value": None,
            "new_value": {"n": seq},
            "reason": "",
            "ip_address": "10.0.0.1",
            "prev_hash": prev,
        }
        fields["hash"] = compute_hash(fields)
        prev = fields["hash"]
        batch.append(AuditEvent(**fields))
        if len(batch) == 5000:
            AuditEvent.objects.bulk_create(batch)
            batch = []
    if batch:
        AuditEvent.objects.bulk_create(batch)


@pytest.mark.req("001:SC-007")
def test_verificacao_de_200_mil_eventos(make_user):
    bulk_chain(TOTAL)
    began = time.perf_counter()
    result = verify_chain()
    elapsed = time.perf_counter() - began
    print(
        f"\nVerificação de {TOTAL} eventos: {elapsed:.1f} s; extrapolado para 1 milhão: {elapsed * 5:.0f} s"
    )
    assert result.status == ChainVerification.Status.INTACT
    assert elapsed * (1_000_000 / TOTAL) < 15 * 60


@pytest.mark.req("001:SC-005")
def test_consulta_e_exportacao_de_um_mes(client, login_as, make_user):
    actor = make_user("volume")
    bulk_chain(TOTAL, actor=actor)
    login_as(Profile.QUALITY)
    today = timezone.localdate()
    params = {
        "usuario": actor.pk,
        "tipo": "audit.exported",
        "de": today - timedelta(days=45),
        "ate": today - timedelta(days=15),
    }
    began = time.perf_counter()
    response = client.get(reverse("audit:trail"), params)
    assert response.status_code == 200
    export = client.get(reverse("audit:export"), {**params, "formato": "csv"})
    size = sum(len(chunk) for chunk in export.streaming_content)
    elapsed = time.perf_counter() - began
    print(
        f"\nConsulta + exportação de um mês ({TOTAL} eventos na base): {elapsed:.1f} s, {size} bytes"
    )
    assert elapsed < 60
