"""Privilégios do papel de banco da aplicação (FR-019, FR-026): sem DELETE, sem UPDATE na trilha."""

import pytest
from django.core.management import call_command
from django.db import ProgrammingError, connection

from sgp.accounts.models import User
from sgp.audit.services import record_event
from sgp.core.db_privileges import append_only_tables
from tests.db_helpers import app_role_exists, run_as_app_role

pytestmark = [pytest.mark.django_db]


@pytest.fixture(autouse=True)
def _require_role():
    if not app_role_exists():
        pytest.skip("Papel da aplicação inexistente neste banco.")


@pytest.mark.req("001:FR-019")
def test_papel_da_aplicacao_nao_altera_nem_apaga_eventos():
    event = record_event("audit.exported", actor=None, new_value={"formato": "csv"})
    with pytest.raises(ProgrammingError, match="permission denied"):
        run_as_app_role("UPDATE audit_auditevent SET reason = 'x' WHERE seq = %s", [event.seq])
    with pytest.raises(ProgrammingError, match="permission denied"):
        run_as_app_role("DELETE FROM audit_auditevent WHERE seq = %s", [event.seq])
    with pytest.raises(ProgrammingError, match="permission denied"):
        run_as_app_role("TRUNCATE audit_auditevent")


@pytest.mark.req("001:FR-026")
def test_papel_da_aplicacao_nao_apaga_cadastros(make_user):
    user = make_user("protegida")
    with pytest.raises(ProgrammingError, match="permission denied"):
        run_as_app_role("DELETE FROM accounts_user WHERE id = %s", [user.pk])
    run_as_app_role("UPDATE accounts_user SET job_title = 'Nova função' WHERE id = %s", [user.pk])


@pytest.mark.req("001:FR-019")
def test_papel_da_aplicacao_inclui_eventos():
    run_as_app_role(
        "INSERT INTO audit_auditevent (seq, occurred_at, actor_username, event_type, object_type, "
        "object_id, object_repr, reason, ip_address, prev_hash, hash) "
        "VALUES (999999, now(), 'teste', 'audit.exported', '', '', '', '', '', %s, %s)",
        ["0" * 64, "f" * 64],
    )


def test_sessoes_podem_ser_apagadas_pelo_logout():
    run_as_app_role("DELETE FROM django_session WHERE session_key = 'inexistente'")


def test_tabelas_append_only_registradas():
    tables = append_only_tables()
    assert {"audit_auditevent", "audit_chainverification", "accounts_loginattempt"} <= set(tables)


@pytest.mark.req("001:FR-019")
def test_trigger_recusa_alteracao_mesmo_pelo_dono():
    event = record_event("audit.exported", actor=None, new_value={"formato": "csv"})
    with pytest.raises(ProgrammingError, match="Registro imutável"):
        with connection.cursor() as cursor:
            cursor.execute("UPDATE audit_auditevent SET reason = 'x' WHERE seq = %s", [event.seq])


def test_comando_reaplica_privilegios(capsys):
    call_command("apply_db_privileges")
    assert "Privilégios aplicados" in capsys.readouterr().out
    assert User.objects.count() >= 0
