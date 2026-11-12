"""Geração de documentos (feature 006): modelos de layout, vínculo de layout por versão de documento,
conteúdo congelado na aprovação, pedidos de geração e documentos gerados (data-model.md)."""

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from sgp.core.models import AppendOnlyModel, ProtectedModel
from sgp.revisions.models import RevisableTemplate
from sgp.signatures.models import DocumentKind


class LayoutTarget(models.TextChoices):
    SUBDOCUMENT = "subdocument", "Subdocumentos"
    CHARTER = "charter", "Termo de Abertura de Projeto"
    BUSINESS_PLAN = "business_plan", "Plano de Negócios"


class LayoutStatus(models.TextChoices):
    DRAFT = "draft", "Rascunho"
    PUBLISHED = "published", "Publicado"
    DISCARDED = "discarded", "Descartado"


class LayoutTemplate(ProtectedModel, RevisableTemplate):
    target = models.CharField("alvo", max_length=20, choices=LayoutTarget.choices)
    version = models.PositiveSmallIntegerField("versão")
    valid_from = models.DateField("início de vigência")
    status = models.CharField(
        "situação", max_length=20, choices=LayoutStatus.choices, default=LayoutStatus.DRAFT
    )
    definition = models.JSONField("definição", default=dict)
    logo = models.ForeignKey(
        "files.StoredFile", on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    note = models.CharField("observação", max_length=200, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    updated_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    published_at = models.DateTimeField(null=True, blank=True)
    row_version = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "modelo de layout"
        verbose_name_plural = "modelos de layout"
        ordering = ["target", "-version"]
        constraints = [
            models.UniqueConstraint(fields=["target", "version"], name="documents_layout_version"),
            models.UniqueConstraint(
                fields=["target"], condition=Q(status="draft"), name="documents_layout_one_draft"
            ),
        ]

    def __str__(self) -> str:
        return f"Layout de {self.get_target_display()} – Versão {self.version_display}"

    @property
    def version_display(self) -> str:
        return f"{self.version:02d}"

    @property
    def is_published(self) -> bool:
        return self.status == LayoutStatus.PUBLISHED


class LayoutBinding(AppendOnlyModel):
    """Layout em que cada versão de documento começou (FR-021)."""

    kind = models.CharField(max_length=20, choices=DocumentKind.choices)
    object_id = models.PositiveBigIntegerField()
    version = models.PositiveSmallIntegerField()
    layout = models.ForeignKey(LayoutTemplate, on_delete=models.PROTECT, related_name="+")
    bound_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "object_id", "version"], name="documents_binding_unique"
            )
        ]


class FrozenRendering(AppendOnlyModel):
    """Conteúdo de renderização congelado na aprovação (FR-017; contrato conteudo-renderizacao.md)."""

    kind = models.CharField(max_length=20, choices=DocumentKind.choices)
    object_id = models.PositiveBigIntegerField()
    version = models.PositiveSmallIntegerField()
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="+")
    layout = models.ForeignKey(LayoutTemplate, on_delete=models.PROTECT, related_name="+")
    content = models.JSONField()
    content_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "object_id", "version"], name="documents_frozen_unique"
            )
        ]


class OutputFormat(models.TextChoices):
    PDF = "pdf", "PDF"
    DOCX = "docx", "DOCX"


class RequestStatus(models.TextChoices):
    QUEUED = "queued", "Na fila"
    RUNNING = "running", "Gerando"
    DONE = "done", "Concluída"
    FAILED = "failed", "Falhou"


ACTIVE_STATUSES = (RequestStatus.QUEUED, RequestStatus.RUNNING)


class GeneratedDocument(AppendOnlyModel):
    """Documento gerado e arquivado (FR-016): nada é apagado nem alterado."""

    kind = models.CharField(max_length=20, choices=DocumentKind.choices)
    object_id = models.PositiveBigIntegerField()
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="+")
    version = models.PositiveSmallIntegerField()
    document_status = models.CharField(max_length=20)
    format = models.CharField(max_length=10, choices=OutputFormat.choices)
    official = models.BooleanField(default=False)
    form_template = models.ForeignKey(
        "formtemplates.FormTemplate",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    layout = models.ForeignKey(LayoutTemplate, on_delete=models.PROTECT, related_name="+")
    data_version = models.PositiveIntegerField(default=0)
    file = models.ForeignKey("files.StoredFile", on_delete=models.PROTECT, related_name="+")
    content_hash = models.CharField(max_length=64)
    file_hash = models.CharField(max_length=64)
    verification_code = models.CharField(max_length=19, blank=True, db_index=True)
    same_as_first = models.BooleanField(null=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    generated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-generated_at", "-pk"]

    @property
    def version_display(self) -> str:
        return f"{self.version:02d}"


class GenerationRequest(ProtectedModel):
    """Pedido de geração em segundo plano (FR-002); a situação aparece na tela."""

    kind = models.CharField(max_length=20, choices=DocumentKind.choices)
    object_id = models.PositiveBigIntegerField()
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="+")
    version = models.PositiveSmallIntegerField()
    format = models.CharField(max_length=10, choices=OutputFormat.choices)
    official = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20, choices=RequestStatus.choices, default=RequestStatus.QUEUED
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    requested_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(blank=True)
    result = models.ForeignKey(
        GeneratedDocument, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )

    class Meta:
        ordering = ["-requested_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "object_id", "version", "format"],
                condition=Q(status__in=["queued", "running"]),
                name="documents_one_active_request",
            )
        ]

    @property
    def is_active(self) -> bool:
        return self.status in ACTIVE_STATUSES

    @property
    def version_display(self) -> str:
        return f"{self.version:02d}"
