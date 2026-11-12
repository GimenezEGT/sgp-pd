"""Assinatura eletrônica, versões aprovadas congeladas e delegação (feature 005)."""

from django.conf import settings
from django.db import models
from django.utils import timezone

from sgp.core.models import AppendOnlyModel, ProtectedModel


class DocumentKind(models.TextChoices):
    SUBDOCUMENT = "subdocument", "Subdocumento"
    CHARTER = "charter", "TAP"
    BUSINESS_PLAN = "business_plan", "Plano de Negócios"


class Meaning(models.TextChoices):
    ELABORATED = "elaborated", "Elaborado"
    REVIEWED = "reviewed", "Revisado"
    APPROVED = "approved", "Aprovado"


class ApprovedVersion(AppendOnlyModel):
    """Conteúdo canônico congelado de cada versão aprovada (sem UPDATE no banco)."""

    kind = models.CharField(max_length=20, choices=DocumentKind.choices)
    object_id = models.PositiveBigIntegerField()
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="+")
    version = models.PositiveSmallIntegerField()
    content = models.JSONField()
    content_hash = models.CharField(max_length=64)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    approved_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["kind", "object_id", "version"]
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "object_id", "version"], name="signatures_unique_approved_version"
            )
        ]
        indexes = [models.Index(fields=["kind", "project"], name="signatures_approved_proj_idx")]

    @property
    def version_display(self) -> str:
        return f"{self.version:02d}"


class Signature(AppendOnlyModel):
    kind = models.CharField(max_length=20, choices=DocumentKind.choices)
    object_id = models.PositiveBigIntegerField()
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="+")
    version = models.PositiveSmallIntegerField()
    content_hash = models.CharField(max_length=64)
    meaning = models.CharField("significado", max_length=20, choices=Meaning.choices)
    signer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    signer_name = models.CharField(max_length=200)
    signer_title = models.CharField(max_length=200, blank=True)
    signed_at = models.DateTimeField(default=timezone.now)
    delegation = models.ForeignKey(
        "ApprovalDelegation", on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )

    class Meta:
        ordering = ["signed_at", "pk"]
        indexes = [models.Index(fields=["kind", "object_id", "version"], name="signatures_doc_idx")]


class SignatureAttempt(AppendOnlyModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    success = models.BooleanField()
    reason = models.CharField(max_length=40, blank=True)
    at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["at", "pk"]


class SignatureLock(ProtectedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]


class ReviewComment(AppendOnlyModel):
    kind = models.CharField(max_length=20, choices=DocumentKind.choices)
    object_id = models.PositiveBigIntegerField()
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="+")
    version = models.PositiveSmallIntegerField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    action = models.CharField(max_length=20, default="returned")
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["created_at", "pk"]


class ApprovalDelegation(ProtectedModel):
    delegator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    delegate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="delegado",
    )
    starts_on = models.DateField("início")
    ends_on = models.DateField("fim")
    reason = models.TextField("motivo")
    created_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    ended_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    end_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-starts_on", "-pk"]

    def __str__(self) -> str:
        return f"Delegação de {self.delegator.get_full_name()} para {self.delegate.get_full_name()}"

    def is_active_on(self, day) -> bool:
        return self.ended_at is None and self.starts_on <= day <= self.ends_on
