"""Qualificações de instalação (IQ) e de operação (OQ) com relatório guardado (FR-011 a FR-013,
SC-003 da feature 014)."""

from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied
from django.core.management import CommandError, call_command
from django.db import DatabaseError, transaction
from django.utils import timezone

from sgp.files.storage import read_verified
from sgp.operations import installation, operation, qualification
from sgp.operations.checks import APPROVED, FAILED, NOT_APPLICABLE
from sgp.operations.models import (
    BackupRun,
    BackupStatus,
    QualificationChannel,
    QualificationKind,
    QualificationRun,
    RestoreStatus,
    RestoreTest,
)


def _by_code(items):
    return {item["codigo"]: item for item in items}


@pytest.fixture
def worker_up(monkeypatch):
    monkeypatch.setattr(installation, "worker_ping", lambda timeout=3.0: ["celery@teste"])
    monkeypatch.setattr(operation, "worker_ping", lambda timeout=3.0: ["celery@teste"])


@pytest.mark.django_db
@pytest.mark.req("014:FR-011")
def test_itens_da_instalacao_com_resultado_e_detalhe(backup_dir, seal_cert, worker_up):
    items = _by_code(installation.run())
    assert list(items) == [f"IQ-{n:02d}" for n in range(1, 25)]
    for item in items.values():
        assert item["resultado"] in {APPROVED, FAILED, NOT_APPLICABLE} and item["detalhe"]
    for code in ("IQ-01", "IQ-02", "IQ-03", "IQ-04", "IQ-05", "IQ-07", "IQ-10", "IQ-12"):
        assert items[code]["resultado"] == APPROVED, items[code]
    for code in ("IQ-13", "IQ-14", "IQ-15", "IQ-17", "IQ-18", "IQ-19", "IQ-20", "IQ-21"):
        assert items[code]["resultado"] == APPROVED, items[code]
    assert "uv.lock" in items["IQ-03"]["detalhe"] and "17" in items["IQ-04"]["detalhe"]


@pytest.mark.django_db
@pytest.mark.req("014:FR-011")
@pytest.mark.req("014:SC-003")
def test_configuracao_invalida_reprova_o_item_com_motivo(
    settings, tmp_path, monkeypatch, backup_dir
):
    settings.DEBUG = True
    settings.SECRET_KEY = "chave-de-dev"
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.AUTH_LDAP_SERVER_URI = ""
    inside = tmp_path / "media" / "copias"
    inside.mkdir(parents=True)
    settings.BACKUP_DIR = str(inside)
    monkeypatch.setattr(
        installation.MigrationExecutor,
        "migration_plan",
        lambda self, targets: [
            (type("M", (), {"app_label": "operations", "name": "9999_x"}), False)
        ],
    )
    items = _by_code(installation.run())
    expected = {
        "IQ-05": "pendente",
        "IQ-07": "depuração ligado",
        "IQ-08": "desenvolvimento",
        "IQ-16": "diretório dos dados",
        "IQ-22": "não configurado",
        "IQ-23": "não configurado",
    }
    for code, reason in expected.items():
        assert items[code]["resultado"] == FAILED, items[code]
        assert reason in items[code]["detalhe"], items[code]
    assert "chave-de-dev" not in str(items)


@pytest.mark.django_db
@pytest.mark.req("014:FR-011")
@pytest.mark.req("014:FR-013")
def test_execucao_guarda_relatorio_imutavel_e_registra(it_admin, analyst, events, worker_up):
    run = qualification.execute(
        QualificationKind.INSTALLATION, by=it_admin, channel=QualificationChannel.COMMAND
    )
    assert run.executed_by == it_admin and run.system_version and run.items
    assert run.passed is (not run.failed_items)
    pdf = read_verified(run.report)
    assert pdf.startswith(b"%PDF-") and run.report.original_name.startswith("qualificacao-IQ-")
    event = events("operations.qualification_executed")[-1]
    assert event.new_value["relatorio_sha256"] == run.report.sha256
    assert event.new_value["reprovados"] == [i["codigo"] for i in run.failed_items]
    from django.db import connection

    from sgp.core.models import ImmutableRecordError

    with pytest.raises(ImmutableRecordError):
        QualificationRun.objects.filter(pk=run.pk).update(passed=not run.passed)
    with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cursor:
        cursor.execute(
            "UPDATE operations_qualificationrun SET passed = NOT passed WHERE id = %s", [run.pk]
        )
    with pytest.raises(PermissionDenied):
        qualification.execute(QualificationKind.INSTALLATION, by=analyst)
    with pytest.raises(CommandError):
        call_command("qualificacao_instalacao", "--usuario", analyst.username)


@pytest.mark.django_db
@pytest.mark.req("014:FR-012")
def test_operacao_sem_alterar_dados(
    it_admin, make_project, seal_cert, worker_up, live_counts, events
):
    make_project()
    now = timezone.now()
    BackupRun.objects.create(
        status=BackupStatus.SUCCESS, started_at=now - timedelta(hours=2), finished_at=now
    )
    RestoreTest.objects.create(status=RestoreStatus.PASSED, started_at=now)
    before = live_counts()
    items = _by_code(operation.run())
    assert live_counts() == before
    for code in ("OQ-01", "OQ-02", "OQ-03", "OQ-05", "OQ-06", "OQ-07", "OQ-08", "OQ-09", "OQ-11"):
        assert items[code]["resultado"] == APPROVED, items[code]
    assert "Recusada pelo banco" in items["OQ-02"]["detalhe"]
    assert items["OQ-04"]["resultado"] in {APPROVED, NOT_APPLICABLE}
    assert items["OQ-10"]["resultado"] == NOT_APPLICABLE
    assert "selado" in items["OQ-06"]["detalhe"]


@pytest.mark.django_db
@pytest.mark.req("014:FR-012")
def test_operacao_reprova_sem_copia_e_sem_teste(quality, seal_cert, worker_up):
    run = qualification.execute(QualificationKind.OPERATION, by=quality)
    failed = {item["codigo"] for item in run.failed_items}
    assert {"OQ-08", "OQ-09"} <= failed and not run.passed
    assert run.channel == QualificationChannel.SCREEN


@pytest.mark.django_db
@pytest.mark.req("014:FR-012")
def test_linha_de_comando_so_para_a_ti(it_admin, quality, seal_cert, worker_up):
    with pytest.raises(CommandError, match="pela tela"):
        call_command("qualificacao_operacao", "--usuario", quality.username)
    assert not QualificationRun.objects.exists()
    with pytest.raises(CommandError, match="reprovada"):
        call_command("qualificacao_operacao", "--usuario", it_admin.username)
    run = QualificationRun.objects.get()
    assert run.channel == QualificationChannel.COMMAND and run.executed_by == it_admin
