"""Gravação de eventos encadeados (FR-018, FR-020)."""

import threading

import pytest
from django.db import connection, transaction

from sgp.accounts.models import User
from sgp.audit.chain import GENESIS_HASH, compute_hash
from sgp.audit.models import AuditEvent, ChainVerification
from sgp.audit.services import SYSTEM_ACTOR, record_event, verify_chain


@pytest.mark.django_db
@pytest.mark.req("001:FR-020")
def test_sequencia_sem_lacunas_e_encadeada():
    first = record_event("audit.exported", actor=None, new_value={"n": 1})
    second = record_event("audit.exported", actor=None, new_value={"n": 2})
    assert (first.seq, second.seq) == (1, 2)
    assert first.prev_hash == GENESIS_HASH
    assert second.prev_hash == first.hash


@pytest.mark.django_db
@pytest.mark.req("001:FR-018")
def test_evento_guarda_campos_obrigatorios(make_user):
    user = make_user("autora")
    event = record_event(
        "accounts.user_updated",
        actor=user,
        obj=user,
        old_value={"job_title": "A"},
        new_value={"job_title": "B"},
        reason="Ajuste",
        project_id=7,
    )
    event = AuditEvent.objects.get(seq=event.seq)
    assert event.actor == user and event.actor_username == "autora"
    assert event.object_type == "accounts.user" and event.object_id == str(user.pk)
    assert event.old_value == {"job_title": "A"} and event.new_value == {"job_title": "B"}
    assert event.reason == "Ajuste" and event.project_id == 7
    assert event.occurred_at.tzinfo is not None


@pytest.mark.django_db
@pytest.mark.req("001:FR-020")
def test_hash_confere_depois_da_ida_e_volta_pelo_banco():
    event = record_event(
        "audit.exported",
        actor=None,
        new_value={
            "texto": "ação",
            "lista": [1, "dois", None, True],
            "aninhado": {"z": 1, "a": {"b": "c"}},
        },
    )
    stored = AuditEvent.objects.get(seq=event.seq)
    assert compute_hash(stored.hash_fields()) == stored.hash


@pytest.mark.django_db
@pytest.mark.req("001:FR-018")
def test_autor_sistema_quando_nao_ha_pessoa():
    event = record_event("audit.exported", actor=None)
    assert event.actor is None and event.actor_username == SYSTEM_ACTOR


@pytest.mark.django_db
def test_tipo_fora_do_catalogo_e_recusado():
    with pytest.raises(ValueError):
        record_event("tipo.inexistente", actor=None)


@pytest.mark.django_db
@pytest.mark.req("001:FR-018")
def test_rollback_desfaz_evento_e_mudanca_juntos():
    with pytest.raises(RuntimeError):
        with transaction.atomic():
            user = User.objects.create_user("rollback")
            record_event("accounts.user_created", actor=None, obj=user)
            raise RuntimeError("falha no meio da operação")
    assert not User.objects.filter(username="rollback").exists()
    assert not AuditEvent.objects.filter(event_type="accounts.user_created").exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.req("001:FR-020")
def test_gravacao_concorrente_mantem_cadeia_unica():
    errors = []

    def worker(number):
        try:
            for index in range(10):
                record_event("audit.exported", actor=None, new_value={"thread": number, "i": index})
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)
        finally:
            connection.close()

    threads = [threading.Thread(target=worker, args=(number,)) for number in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors
    assert list(AuditEvent.objects.order_by("seq").values_list("seq", flat=True)) == list(
        range(1, 41)
    )
    result = verify_chain()
    assert result.status == ChainVerification.Status.INTACT
