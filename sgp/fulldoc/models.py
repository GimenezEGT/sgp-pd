"""Documento completo do projeto (data-model.md da feature 009)."""

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from sgp.core.models import AppendOnlyModel, ProtectedModel

USER = settings.AUTH_USER_MODEL
NOTEBOOK_SUMMARY = "resumido"
NOTEBOOK_FULL = "completo"


class RequestStatus(models.TextChoices):
    QUEUED = "queued", "Na fila"
    RUNNING = "running", "Gerando"
    DONE = "done", "Concluído"
    FAILED = "failed", "Falhou"


ACTIVE_STATUSES = (RequestStatus.QUEUED, RequestStatus.RUNNING)


class FinalVersionReason(models.TextChoices):
    APPROVAL = "approval", "Aprovação"
    RECOMPOSITION = "recomposition", "Recomposição"
    RECONSTRUCTION = "reconstruction", "Reconstruída"


class FinalDocumentVersion(AppendOnlyModel):
    """Versão do documento final do projeto (feature 016): nasce com cada aprovação de parte e
    guarda a mudança e a composição completa; nada é alterado nem apagado."""

    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="+")
    number = models.PositiveIntegerField("número")
    created_at = models.DateTimeField("registrada em", default=timezone.now)
    registered_by = models.ForeignKey(
        USER,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="aprovada ou registrada por",
    )
    reason = models.CharField("motivo", max_length=20, choices=FinalVersionReason.choices)
    changes = models.JSONField("mudanças", default=list)
    composition = models.JSONField("composição", default=list)
    composition_hash = models.CharField("resumo da composição", max_length=64)

    class Meta:
        verbose_name = "versão do documento final"
        verbose_name_plural = "versões do documento final"
        ordering = ["project", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "number"], name="fulldoc_final_version_unique"
            )
        ]

    def __str__(self) -> str:
        code = self.project.code or self.project.title
        return f"Documento final {code} – versão {self.number:02d}"

    @property
    def number_display(self) -> str:
        return f"{self.number:02d}"

    @property
    def changes_text(self) -> str:
        return "; ".join(change_text(change) for change in self.changes)


def change_text(change: dict) -> str:
    before = f"{change['de']:02d}" if change.get("de") else "—"
    return f"{change['parte']}: {before} → {change['para']:02d}"


class FullDocument(AppendOnlyModel):
    """Documento completo gerado e arquivado: nada é apagado nem alterado."""

    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="+")
    project_version = models.PositiveSmallIntegerField("versão do projeto", default=0)
    options = models.JSONField("opções")
    with_financials = models.BooleanField("contém dados financeiros", default=False)
    official = models.BooleanField("oficial", default=False)
    pending = models.JSONField("pendências na geração", default=list)
    composition_hash = models.CharField("resumo da composição", max_length=64, db_index=True)
    layout = models.ForeignKey(
        "documents.LayoutTemplate", on_delete=models.PROTECT, related_name="+"
    )
    file = models.ForeignKey("files.StoredFile", on_delete=models.PROTECT, related_name="+")
    content_hash = models.CharField("resumo do PDF antes do selo", max_length=64)
    file_hash = models.CharField("resumo do arquivo", max_length=64)
    verification_code = models.CharField(max_length=19, blank=True, db_index=True)
    pages = models.PositiveIntegerField("páginas", default=0)
    generated_by = models.ForeignKey(USER, on_delete=models.PROTECT, related_name="+")
    generated_at = models.DateTimeField("gerado em", default=timezone.now)
    final_version = models.ForeignKey(
        FinalDocumentVersion,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="versão do documento final",
    )

    class Meta:
        verbose_name = "documento completo do projeto"
        verbose_name_plural = "documentos completos do projeto"
        ordering = ["-generated_at", "-pk"]

    def __str__(self) -> str:
        situation = "oficial" if self.official else "rascunho"
        code = self.project.code or self.project.title
        if self.final_version_id:
            return (
                f"Documento completo {code} – versão {self.final_version.number:02d} "
                f"do documento final ({situation})"
            )
        return f"Documento completo {code} – versão {self.project_version:02d} ({situation})"

    @property
    def notebook_label(self) -> str:
        return "completo" if self.options.get("caderno") == NOTEBOOK_FULL else "resumido"


class FullDocumentRequest(ProtectedModel):
    """Pedido de geração em segundo plano, com progresso visível."""

    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="+")
    project_version = models.PositiveSmallIntegerField("versão do projeto", default=0)
    options = models.JSONField("opções")
    with_financials = models.BooleanField(default=False)
    status = models.CharField(
        max_length=10, choices=RequestStatus.choices, default=RequestStatus.QUEUED
    )
    progress = models.PositiveSmallIntegerField(default=0)
    step = models.CharField(max_length=120, blank=True)
    requested_by = models.ForeignKey(USER, on_delete=models.PROTECT, related_name="+")
    requested_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(blank=True)
    result = models.ForeignKey(
        FullDocument, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    reused = models.BooleanField(default=False)

    class Meta:
        ordering = ["-requested_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["project"],
                condition=Q(status__in=["queued", "running"]),
                name="fulldoc_one_active_request",
            )
        ]

    @property
    def is_active(self) -> bool:
        return self.status in ACTIVE_STATUSES
