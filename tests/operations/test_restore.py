"""Teste de restauração num banco isolado (C1 a C6), danos, banco que sobrou e conferência de cópia
em dia (FR-006 a FR-008, SC-001, SC-002 da feature 014)."""

import json
from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone

from sgp.audit.models import AuditEvent
from sgp.operations import backup, restore
from sgp.operations.models import BackupRun, BackupStatus, RestoreStatus

OWN_TABLES = {"operations_restoretest", "audit_auditevent", "audit_auditchainstate"}


def _codes(test):
    return {check["codigo"]: check["aprovado"] for check in test.checks}


@pytest.mark.django_db(transaction=True)
@pytest.mark.req("014:FR-006")
@pytest.mark.req("014:SC-001")
def test_restauracao_aprovada_sem_tocar_no_banco_em_uso(
    backup_dir, it_admin, stored_files, live_counts, restore_db_exists, monkeypatch, events
):
    stored_files(2)
    original = backup.subprocess.run

    def with_write_during_dump(*args, **kwargs):
        with backup.owner_connect(autocommit=True) as conn:
            conn.execute(
                "INSERT INTO django_session (session_key, session_data, expire_date) "
                "VALUES ('sessao-depois-do-instantaneo', 'x', now() + interval '1 day')"
            )
        return original(*args, **kwargs)

    monkeypatch.setattr(backup.subprocess, "run", with_write_during_dump)
    copy = backup.run_backup()
    monkeypatch.setattr(backup.subprocess, "run", original)
    assert copy.status == BackupStatus.SUCCESS
    before = live_counts()
    test = restore.run_restore_test(by=it_admin)
    after = live_counts()
    assert test.status == RestoreStatus.PASSED, test.error
    assert _codes(test) == {code: True for code in ("C1", "C2", "C3", "C4", "C5", "C6")}
    assert test.backup == copy and not restore_db_exists()
    assert {t: n for t, n in before.items() if t not in OWN_TABLES} == {
        t: n for t, n in after.items() if t not in OWN_TABLES
    }
    event = events("operations.restore_tested")[-1]
    assert event.new_value["aprovado"] is True and event.new_value["copia"] == copy.label
    assert not mail.outbox


@pytest.mark.django_db(transaction=True)
@pytest.mark.req("014:FR-006")
@pytest.mark.req("014:FR-008")
@pytest.mark.req("014:SC-002")
def test_danos_reprovam_e_avisam(backup_dir, it_admin, stored_files):
    files = stored_files(2)
    copy = backup.run_backup()
    folder = backup_dir / "copias" / copy.label
    pool_file = backup.pool_path(files[0].sha256)
    original_file = pool_file.read_bytes()
    pool_file.write_bytes(b"%PDF-1.4\n% conteudo adulterado\n")
    altered = restore.run_restore_test()
    assert altered.status == RestoreStatus.FAILED and _codes(altered)["C6"] is False
    assert "alterados" in altered.error and files[0].sha256[:12] in altered.error
    assert "Teste de restauração reprovado" in mail.outbox[-1].subject
    pool_file.unlink()
    missing = restore.run_restore_test()
    assert _codes(missing)["C6"] is False and "ausentes" in missing.error
    pool_file.write_bytes(original_file)
    manifest_path = folder / "manifesto.json"
    original_manifest = manifest_path.read_bytes()
    manifest = json.loads(original_manifest)
    manifest["tabelas"]["files_storedfile"] = 99
    manifest_path.write_bytes(json.dumps(manifest).encode())
    tampered = restore.run_restore_test()
    assert _codes(tampered) == {"C1": False} and tampered.status == RestoreStatus.FAILED
    manifest_path.write_bytes(original_manifest)
    dump = folder / "banco.dump"
    data = dump.read_bytes()
    dump.write_bytes(data[:-10] + b"0123456789")
    broken = restore.run_restore_test()
    assert _codes(broken) == {"C1": True, "C2": False}
    dump.write_bytes(data)
    assert restore.run_restore_test().status == RestoreStatus.PASSED
    assert len(mail.outbox) == 4


@pytest.mark.django_db(transaction=True)
@pytest.mark.req("014:FR-006")
def test_sem_copia_reprova_e_banco_que_sobrou_e_descartado(backup_dir, it_admin, restore_db_exists):
    from psycopg import sql

    empty = restore.run_restore_test()
    assert empty.status == RestoreStatus.FAILED and empty.backup is None
    assert "Não há cópia" in empty.error
    with backup.owner_connect(autocommit=True) as conn:
        conn.execute(
            sql.SQL("CREATE DATABASE {}").format(sql.Identifier(restore.restore_db_name()))
        )
    assert restore_db_exists()
    assert backup.run_backup().status == BackupStatus.SUCCESS
    assert restore.run_restore_test().status == RestoreStatus.PASSED
    assert not restore_db_exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.req("014:FR-006")
def test_um_teste_por_vez(backup_dir):
    with backup.AdvisoryLock(restore.RESTORE_LOCK, "ocupado"):
        with pytest.raises(restore.RestoreBusy):
            restore.run_restore_test()


@pytest.mark.django_db
@pytest.mark.req("014:FR-008")
def test_conferencia_de_copia_em_dia(
    it_admin, settings, events, django_capture_on_commit_callbacks
):
    settings.BACKUP_MAX_AGE_HOURS = 26
    with django_capture_on_commit_callbacks(execute=True):
        assert restore.check_freshness() is False
    assert "Cópia de segurança atrasada" in mail.outbox[-1].subject
    assert events("operations.backup_stale")
    old = BackupRun.objects.create(
        status=BackupStatus.SUCCESS,
        started_at=timezone.now() - timedelta(hours=30),
        finished_at=timezone.now() - timedelta(hours=29),
    )
    with django_capture_on_commit_callbacks(execute=True):
        assert restore.check_freshness() is False
    assert old.label == "" and len(mail.outbox) == 2
    BackupRun.objects.create(
        status=BackupStatus.SUCCESS,
        started_at=timezone.now() - timedelta(hours=2),
        finished_at=timezone.now() - timedelta(hours=1),
    )
    with django_capture_on_commit_callbacks(execute=True):
        assert restore.check_freshness() is True
    assert len(mail.outbox) == 2
    assert AuditEvent.objects.filter(event_type="operations.backup_stale").count() == 2


@pytest.mark.django_db(transaction=True)
@pytest.mark.req("014:FR-006")
@pytest.mark.req("014:SC-002")
def test_trilha_adulterada_reprova_c5_e_aponta_incidente_existente(backup_dir, it_admin):
    from sgp.audit.services import record_event, verify_chain
    from tests.db_helpers import tamper

    record_event("audit.exported", actor=it_admin, new_value={"n": 1})
    record_event("audit.exported", actor=it_admin, new_value={"n": 2})
    seq = AuditEvent.objects.order_by("seq").first().seq
    tamper("UPDATE audit_auditevent SET reason = 'adulterado' WHERE seq = %s", [seq])
    verify_chain()
    assert backup.run_backup().status == BackupStatus.SUCCESS
    test = restore.run_restore_test()
    codes = _codes(test)
    assert codes["C5"] is False and all(codes[c] for c in ("C1", "C2", "C3", "C4", "C6"))
    detail = next(c["detalhe"] for c in test.checks if c["codigo"] == "C5")
    assert f"evento {seq}" in detail and "incidente existente" in detail
