"""Cópia de segurança diária: manifesto, acervo, destino, concorrência e retenção (FR-001 a FR-005,
FR-007, FR-008 da feature 014)."""

import json
import os
from datetime import datetime, timedelta

import pytest
from django.core import mail
from django.utils import timezone

from sgp.audit.models import AuditEvent
from sgp.files.models import StoredFile
from sgp.operations import backup
from sgp.operations.models import BackupRun, BackupStatus, RunKind


@pytest.mark.django_db(transaction=True)
@pytest.mark.req("014:FR-001")
@pytest.mark.req("014:FR-002")
@pytest.mark.req("014:FR-004")
@pytest.mark.req("014:FR-007")
def test_copia_com_manifesto_acervo_e_trilha(backup_dir, it_admin, stored_files, events):
    from sgp.audit.services import record_event

    files = stored_files(2)
    record_event("audit.exported", actor=it_admin, new_value={"motivo": "evento fictício"})
    record = backup.run_backup(kind=RunKind.MANUAL, by=it_admin)
    assert record.status == BackupStatus.SUCCESS, record.error
    folder = backup_dir / "copias" / record.label
    manifest_bytes = (folder / "manifesto.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    assert backup.sha256_file(folder / "manifesto.json") == record.manifest_sha256
    assert (
        manifest["banco"]["sha256"]
        == record.database_sha256
        == backup.sha256_file(folder / "banco.dump")
    )
    assert manifest["banco"]["tamanho"] == record.database_size > 0
    assert manifest["sistema"]["versao"] and record.system_version
    assert manifest["tabelas"]["files_storedfile"] == StoredFile.objects.count() == 2
    completed = AuditEvent.objects.get(event_type="operations.backup_completed")
    assert manifest["trilha"]["seq"] == completed.seq - 1 == record.audit_head_seq
    assert {sha for sha, _ in manifest["arquivos"]["lista"]} == {f.sha256 for f in files}
    for stored in files:
        copy = backup.pool_path(stored.sha256)
        assert copy.is_file() and backup.sha256_file(copy) == stored.sha256
    assert record.files_total == 2 and record.files_new == 2 and record.monthly
    second = backup.run_backup()
    assert second.status == BackupStatus.SUCCESS
    assert second.files_total == 2 and second.files_new == 0 and not second.monthly
    assert len(events("operations.backup_completed")) == 2
    assert completed.new_value["manifesto_sha256"] == record.manifest_sha256


@pytest.mark.django_db(transaction=True)
@pytest.mark.req("014:FR-001")
def test_gravacao_durante_a_copia_nao_e_bloqueada_e_fica_fora(backup_dir, it_admin, monkeypatch):
    from django.db import connection

    original = backup.subprocess.run
    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM django_session")
        before = cursor.fetchone()[0]

    def run_with_concurrent_write(*args, **kwargs):
        with backup.owner_connect(autocommit=True) as conn:
            conn.execute(
                "INSERT INTO django_session (session_key, session_data, expire_date) "
                "VALUES (%s, %s, now() + interval '1 day')",
                ["sessao-concorrente-ficticia", "x"],
            )
        return original(*args, **kwargs)

    monkeypatch.setattr(backup.subprocess, "run", run_with_concurrent_write)
    record = backup.run_backup()
    assert record.status == BackupStatus.SUCCESS
    assert record.table_counts["django_session"] == before
    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM django_session")
        assert cursor.fetchone()[0] == before + 1


@pytest.mark.django_db(transaction=True)
@pytest.mark.req("014:FR-003")
@pytest.mark.req("014:FR-008")
def test_destino_invalido_reprova_e_avisa(settings, tmp_path, it_admin, events):
    settings.BACKUP_DIR = str(tmp_path / "nao-existe")
    failed = backup.run_backup()
    assert failed.status == BackupStatus.FAILED and "inexistente" in failed.error
    assert mail.outbox and mail.outbox[-1].to == ["ti@teste.local"]
    assert "Falha na cópia de segurança" in mail.outbox[-1].subject
    inside = tmp_path / "media" / "copias"
    inside.mkdir(parents=True)
    settings.BACKUP_DIR = str(inside)
    assert "diretório dos dados" in backup.run_backup().error
    settings.BACKUP_DIR = str(tmp_path)
    assert "diretório dos dados" in backup.run_backup().error
    locked = tmp_path / "sem-gravacao"
    locked.mkdir()
    os.chmod(locked, 0o500)
    settings.BACKUP_DIR = str(locked)
    try:
        assert "permissão de gravação" in backup.run_backup().error
    finally:
        os.chmod(locked, 0o700)
    assert len(events("operations.backup_failed")) == 4


@pytest.mark.django_db(transaction=True)
@pytest.mark.req("014:FR-004")
def test_arquivo_ausente_reprova_a_copia(backup_dir, it_admin, stored_files, settings):
    from pathlib import Path

    stored = stored_files(1)[0]
    (Path(settings.MEDIA_ROOT) / stored.storage_name).unlink()
    record = backup.run_backup()
    assert record.status == BackupStatus.FAILED
    assert stored.sha256[:12] in record.error and "ausente" in record.error
    folder = backup_dir / "copias" / record.label
    manifest = json.loads((folder / "manifesto.json").read_bytes())
    assert manifest["arquivos"]["problemas"] == [[stored.sha256, "ausente"]]
    assert record.database_sha256 == backup.sha256_file(folder / "banco.dump")
    assert backup.latest_success() is None


@pytest.mark.django_db(transaction=True)
@pytest.mark.req("014:FR-004")
def test_arquivo_alterado_nao_entra_no_acervo(backup_dir, it_admin, stored_files, settings):
    from pathlib import Path

    good, bad = stored_files(2)
    path = Path(settings.MEDIA_ROOT) / bad.storage_name
    path.write_bytes(path.read_bytes() + b"adulterado")
    record = backup.run_backup()
    assert record.status == BackupStatus.FAILED and "conteúdo diferente" in record.error
    assert bad.sha256[:12] in record.error
    assert backup.pool_path(good.sha256).is_file() and not backup.pool_path(bad.sha256).exists()
    manifest = json.loads((backup_dir / "copias" / record.label / "manifesto.json").read_bytes())
    assert manifest["arquivos"]["problemas"] == [[bad.sha256, "alterado"]]


@pytest.mark.django_db(transaction=True)
@pytest.mark.req("014:FR-001")
def test_uma_copia_por_vez(backup_dir):
    with backup.AdvisoryLock(backup.BACKUP_LOCK, "ocupado"):
        assert backup.is_running()
        with pytest.raises(backup.BackupBusy):
            backup.run_backup()
    assert not BackupRun.objects.exists() and not backup.is_running()


@pytest.mark.django_db
@pytest.mark.req("014:FR-005")
def test_retencao_mantem_mensal_e_registra_remocao(backup_dir, events, settings):
    settings.BACKUP_KEEP_DAYS = 35
    now = timezone.now()

    def make(days, label, **extra):
        (backup_dir / "copias" / label).mkdir(parents=True)
        return BackupRun.objects.create(
            status=extra.pop("status", BackupStatus.SUCCESS),
            started_at=now - timedelta(days=days),
            label=label,
            **extra,
        )

    old_daily = make(40, "antiga-diaria")
    old_monthly = make(60, "antiga-mensal", monthly=True)
    recent = make(10, "recente")
    failed = make(20, "falhou", status=BackupStatus.FAILED)
    old_failed = make(50, "falhou-antiga", status=BackupStatus.FAILED)
    removed = backup.prune(now)
    assert [r.pk for r in removed] == [old_failed.pk, old_daily.pk]
    old_daily.refresh_from_db()
    assert old_daily.removed_at is not None
    assert not (backup_dir / "copias" / "antiga-diaria").exists()
    for kept in (old_monthly, recent, failed):
        kept.refresh_from_db()
        assert kept.removed_at is None and (backup_dir / "copias" / kept.label).exists()
    assert len(events("operations.backup_removed")) == 2
    assert backup.prune(now) == []


@pytest.mark.django_db
@pytest.mark.req("014:FR-005")
def test_primeira_copia_bem_sucedida_do_mes_e_a_mensal():
    from sgp.operations.backup import _first_of_month

    base = timezone.make_aware(datetime(2026, 11, 3, 1, 0))
    first = BackupRun.objects.create(status=BackupStatus.SUCCESS, started_at=base)
    later = BackupRun.objects.create(started_at=base + timedelta(days=7))
    next_month = BackupRun.objects.create(started_at=base + timedelta(days=30))
    assert _first_of_month(later) is False
    assert _first_of_month(next_month) is True
    assert _first_of_month(first) is True
