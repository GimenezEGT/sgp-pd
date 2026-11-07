"""Verificação da cadeia: adulterações feitas direto no banco são reveladas (FR-020, FR-021, SC-003)."""

import pytest

from sgp.audit.models import AuditEvent, ChainVerification
from sgp.audit.services import integrity_alert_active, record_event, verify_chain
from tests.db_helpers import tamper

pytestmark = [pytest.mark.django_db, pytest.mark.req("001:FR-021"), pytest.mark.req("001:SC-003")]


def make_events(total=5):
    return [record_event("audit.exported", actor=None, new_value={"n": n}) for n in range(total)]


def kinds(result, seq=None):
    return {item["kind"] for item in result.breaks if seq is None or item["seq"] == seq}


def test_trilha_integra():
    make_events(5)
    result = verify_chain()
    assert result.status == ChainVerification.Status.INTACT
    assert result.events_checked == 5 and result.head_seq == 5 and result.breaks == []
    verified = AuditEvent.objects.get(event_type="audit.chain_verified")
    assert verified.new_value == {"situacao": "intact", "eventos": 5, "ultimo_seq": 5, "quebras": 0}


@pytest.mark.req("001:FR-020")
def test_conteudo_alterado_no_banco_e_apontado():
    make_events(5)
    tamper("UPDATE audit_auditevent SET reason = 'adulterado' WHERE seq = 3")
    result = verify_chain()
    assert result.status == ChainVerification.Status.BROKEN
    assert kinds(result, 3) == {"content_altered"}
    assert integrity_alert_active()


@pytest.mark.req("001:FR-020")
def test_valor_json_alterado_no_banco_e_apontado():
    make_events(4)
    tamper("""UPDATE audit_auditevent SET new_value = '{"n": 99}' WHERE seq = 2""")
    assert kinds(verify_chain(), 2) == {"content_altered"}


@pytest.mark.req("001:FR-020")
def test_exclusao_no_meio_e_apontada():
    make_events(5)
    tamper("DELETE FROM audit_auditevent WHERE seq = 3")
    result = verify_chain()
    assert {"sequence_gap", "chain_broken"} <= kinds(result, 4)


@pytest.mark.req("001:FR-020")
def test_insercao_forjada_e_apontada():
    events = make_events(3)
    tamper(
        "INSERT INTO audit_auditevent (seq, occurred_at, actor_username, event_type, object_type, "
        "object_id, object_repr, reason, ip_address, prev_hash, hash) VALUES "
        "(4, now(), 'intruso', 'audit.exported', '', '', '', 'forjado', '', %s, %s)",
        ["1" * 64, "2" * 64],
    )
    result = verify_chain()
    assert {"content_altered", "chain_broken"} <= kinds(result, 4)
    assert events[-1].seq == 3


def test_exclusao_do_trecho_final_e_revelada_pelo_ponto_de_controle():
    make_events(5)
    first = verify_chain()
    assert first.status == ChainVerification.Status.INTACT and first.head_seq == 5
    tamper("DELETE FROM audit_auditevent WHERE seq >= 5")
    result = verify_chain()
    assert "checkpoint_missing" in kinds(result, 5)


def test_alteracao_do_ponto_de_controle_e_revelada():
    make_events(3)
    verify_chain()
    tamper("UPDATE audit_auditevent SET hash = %s WHERE seq = 3", ["9" * 64])
    result = verify_chain()
    assert "checkpoint_mismatch" in kinds(result, 3)


def test_nova_verificacao_integra_remove_o_alerta():
    make_events(2)
    tamper("UPDATE audit_auditevent SET reason = 'x' WHERE seq = 1")
    verify_chain()
    assert integrity_alert_active()
    tamper("UPDATE audit_auditevent SET reason = '' WHERE seq = 1")
    verify_chain()
    assert not integrity_alert_active()


def test_resultado_da_verificacao_e_protegido(make_user):
    from django.db import ProgrammingError, connection

    make_events(1)
    result = verify_chain(triggered_by=make_user("auditora"))
    with pytest.raises(ProgrammingError, match="Registro imutável"):
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE audit_chainverification SET status = 'intact' WHERE id = %s", [result.pk]
            )
