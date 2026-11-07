"""Modelo de formulário versionado (feature 004): definição em JSON, imutável depois de publicada."""

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from sgp.core.models import ProtectedModel


class TemplateStatus(models.TextChoices):
    DRAFT = "draft", "Rascunho"
    PUBLISHED = "published", "Publicado"


class FormTemplate(ProtectedModel):
    subdocument_type = models.ForeignKey(
        "vocab.Term",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="tipo de subdocumento",
    )
    form_version = models.PositiveSmallIntegerField("versão do formulário")
    reference = models.CharField("referência", max_length=200)
    valid_from = models.DateField("início de vigência")
    status = models.CharField(
        "situação", max_length=20, choices=TemplateStatus.choices, default=TemplateStatus.DRAFT
    )
    definition = models.JSONField("definição", default=dict)
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
    published_note = models.CharField(max_length=200, blank=True)
    row_version = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "modelo de formulário"
        verbose_name_plural = "modelos de formulário"
        ordering = ["subdocument_type__position", "-form_version"]
        constraints = [
            models.UniqueConstraint(
                fields=["subdocument_type", "form_version"], name="formtemplates_unique_version"
            ),
            models.UniqueConstraint(
                fields=["subdocument_type"],
                condition=Q(status="draft"),
                name="formtemplates_one_draft",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.subdocument_type.label} – Formulário Versão {self.version_display}"

    @property
    def version_display(self) -> str:
        return f"{self.form_version:02d}"

    @property
    def is_published(self) -> bool:
        return self.status == TemplateStatus.PUBLISHED

    @property
    def footer(self) -> str:
        return f"Formulário Versão: {self.version_display}. Referência: {self.reference}"

    @property
    def cover(self) -> dict:
        return self.definition.get("cover", {})

    @property
    def topics(self) -> list[dict]:
        return self.definition.get("topics", [])

    def topic(self, key: str) -> dict | None:
        return next((topic for topic in self.topics if topic.get("key") == key), None)
