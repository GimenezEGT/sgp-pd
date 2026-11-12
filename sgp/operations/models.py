"""Cópias de segurança, testes de restauração e qualificações (data-model.md da feature 014)."""

from django.conf import settings
from django.db import models
from django.utils import timezone

from sgp.core.models import AppendOnlyModel, ProtectedModel


class RunKind(models.TextChoices):
    SCHEDULED = "scheduled", "Agendada"
    MANUAL = "manual", "Pedida"


class BackupStatus(models.TextChoices):
    RUNNING = "running", "Em andamento"
    SUCCESS = "success", "Bem-sucedida"
    FAILED = "failed", "Falhou"


class RestoreStatus(models.TextChoices):
    RUNNING = "running", "Em andamento"
    PASSED = "passed", "Aprovado"
    FAILED = "failed", "Reprovado"


class BackupRun(ProtectedModel):
    kind = models.CharField(
        "tipo", max_length=16, choices=RunKind.choices, default=RunKind.SCHEDULED
    )
    status = models.CharField(
        "situação", max_length=16, choices=BackupStatus.choices, default=BackupStatus.RUNNING
    )
    label = models.CharField("pasta no destino", max_length=40, blank=True)
    started_at = models.DateTimeField("início", default=timezone.now)
    finished_at = models.DateTimeField("fim", null=True, blank=True)
    system_version = models.CharField("versão do sistema", max_length=80, blank=True)
    database_size = models.PositiveBigIntegerField("tamanho do banco copiado", default=0)
    database_sha256 = models.CharField("resumo do banco copiado", max_length=64, blank=True)
    server_version = models.CharField("versão do PostgreSQL", max_length=60, blank=True)
    table_counts = models.JSONField("linhas por tabela", default=dict, blank=True)
    audit_head_seq = models.PositiveBigIntegerField(
        "último evento da trilha", null=True, blank=True
    )
    audit_head_hash = models.CharField("resumo do último evento", max_length=64, blank=True)
    files_total = models.PositiveIntegerField("arquivos", default=0)
    files_new = models.PositiveIntegerField("arquivos novos no acervo", default=0)
    files_bytes = models.PositiveBigIntegerField("bytes dos arquivos", default=0)
    manifest_sha256 = models.CharField("resumo do manifesto", max_length=64, blank=True)
    monthly = models.BooleanField("cópia mensal mantida", default=False)
    removed_at = models.DateTimeField("removida pela retenção em", null=True, blank=True)
    error = models.TextField("motivo da falha", blank=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="pedida por",
    )

    class Meta:
        verbose_name = "cópia de segurança"
        verbose_name_plural = "cópias de segurança"
        ordering = ["-started_at", "-pk"]

    def __str__(self) -> str:
        return f"Cópia de segurança {self.label or self.pk}"

    @property
    def database_size_display(self) -> str:
        return _size(self.database_size)

    @property
    def files_bytes_display(self) -> str:
        return _size(self.files_bytes)


class RestoreTest(ProtectedModel):
    backup = models.ForeignKey(
        BackupRun,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="restore_tests",
        verbose_name="cópia testada",
    )
    kind = models.CharField(
        "tipo", max_length=16, choices=RunKind.choices, default=RunKind.SCHEDULED
    )
    status = models.CharField(
        "situação", max_length=16, choices=RestoreStatus.choices, default=RestoreStatus.RUNNING
    )
    started_at = models.DateTimeField("início", default=timezone.now)
    finished_at = models.DateTimeField("fim", null=True, blank=True)
    checks = models.JSONField("conferências", default=list, blank=True)
    error = models.TextField("motivo da reprovação", blank=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="pedido por",
    )

    class Meta:
        verbose_name = "teste de restauração"
        verbose_name_plural = "testes de restauração"
        ordering = ["-started_at", "-pk"]

    def __str__(self) -> str:
        return f"Teste de restauração {self.pk}"


class QualificationKind(models.TextChoices):
    INSTALLATION = "installation", "Qualificação de instalação (IQ)"
    OPERATION = "operation", "Qualificação de operação (OQ)"


class QualificationChannel(models.TextChoices):
    COMMAND = "command", "Linha de comando"
    SCREEN = "screen", "Tela"


class QualificationRun(AppendOnlyModel):
    kind = models.CharField("tipo", max_length=16, choices=QualificationKind.choices)
    channel = models.CharField("canal", max_length=16, choices=QualificationChannel.choices)
    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="executada por",
    )
    started_at = models.DateTimeField("início")
    finished_at = models.DateTimeField("fim")
    system_version = models.CharField("versão do sistema", max_length=80, blank=True)
    items = models.JSONField("itens", default=list)
    passed = models.BooleanField("aprovada")
    report = models.ForeignKey(
        "files.StoredFile",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="relatório",
    )

    class Meta:
        verbose_name = "execução de qualificação"
        verbose_name_plural = "execuções de qualificação"
        ordering = ["-finished_at", "-pk"]

    def __str__(self) -> str:
        return f"{self.get_kind_display()} {self.pk}"

    @property
    def failed_items(self) -> list[dict]:
        return [item for item in self.items if item.get("resultado") == "reprovado"]


def _size(value: int) -> str:
    size = float(value or 0)
    for unit in ("bytes", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            text = f"{size:.0f}" if unit == "bytes" else f"{size:.1f}"
            return f"{text.replace('.', ',')} {unit}"
        size /= 1024
    return ""
