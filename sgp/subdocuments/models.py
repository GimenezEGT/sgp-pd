"""Subdocumentos do projeto preenchidos a partir da versão de modelo usada (feature 004)."""

from django.conf import settings
from django.db import models
from django.utils import timezone

from sgp.core.models import AppendOnlyModel, ProtectedModel

ENTRY = "entrada"
CHANGE = "alteracao"
FINAL_CHECK = "verificacao-final"


class SubdocumentStatus(models.TextChoices):
    DRAFT = "draft", "Rascunho"
    IN_REVIEW = "in_review", "Em revisão"
    RETURNED = "returned", "Devolvido"
    APPROVED = "approved", "Aprovado"


EDITABLE_STATUSES = (SubdocumentStatus.DRAFT, SubdocumentStatus.RETURNED)


class Subdocument(ProtectedModel):
    project = models.ForeignKey(
        "projects.Project", on_delete=models.PROTECT, related_name="subdocuments"
    )
    subdocument_type = models.ForeignKey(
        "vocab.Term", on_delete=models.PROTECT, related_name="+", verbose_name="tipo"
    )
    sequence = models.PositiveSmallIntegerField("número", default=1)
    template = models.ForeignKey(
        "formtemplates.FormTemplate", on_delete=models.PROTECT, related_name="subdocuments"
    )
    version = models.PositiveSmallIntegerField("versão do documento", default=1)
    status = models.CharField(
        "situação",
        max_length=20,
        choices=SubdocumentStatus.choices,
        default=SubdocumentStatus.DRAFT,
    )
    data = models.JSONField("dados", default=dict)
    unmapped_data = models.JSONField("dados não migrados", default=dict, blank=True)
    changed_version = models.PositiveSmallIntegerField("versão alterada", null=True, blank=True)
    new_version = models.PositiveSmallIntegerField("nova versão", null=True, blank=True)
    review_requested_by = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="review_requests",
        verbose_name="marcado para revisão pela Alteração",
    )
    review_requested_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    updated_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    row_version = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "subdocumento"
        verbose_name_plural = "subdocumentos"
        ordering = ["subdocument_type__position", "sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "subdocument_type", "sequence"],
                name="subdocuments_unique_per_project",
            )
        ]

    def __str__(self) -> str:
        label = self.subdocument_type.label
        if self.subdocument_type.code == CHANGE:
            label = f"{label} {self.sequence}"
        return f"{label} – versão {self.version_display}"

    @property
    def version_display(self) -> str:
        return f"{self.version:02d}"

    @property
    def is_draft(self) -> bool:
        """Editável: rascunho ou devolvido na revisão (feature 005)."""
        return self.status in EDITABLE_STATUSES

    @property
    def is_approved(self) -> bool:
        return self.status == SubdocumentStatus.APPROVED

    def topic_data(self, key: str) -> dict:
        topic = (self.data or {}).get("topics", {}).get(key) or {}
        return {
            "na": bool(topic.get("na")),
            "justification": topic.get("justification", ""),
            "values": topic.get("values", {}) or {},
        }


class FlowAuthorization(AppendOnlyModel):
    """Autorização do Gestor de P&D para criar subdocumento fora da ordem recomendada."""

    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="+")
    subdocument_type = models.ForeignKey("vocab.Term", on_delete=models.PROTECT, related_name="+")
    missing_requirement = models.CharField(max_length=200)
    reason = models.TextField("motivo")
    authorized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    authorized_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "autorização de fluxo"
        ordering = ["-authorized_at"]


class FlowAuthorizationUse(AppendOnlyModel):
    """Uso (único) de uma autorização de fluxo na criação de um subdocumento."""

    authorization = models.OneToOneField(
        FlowAuthorization, on_delete=models.PROTECT, related_name="use"
    )
    subdocument = models.OneToOneField(
        Subdocument, on_delete=models.PROTECT, related_name="flow_authorization_use"
    )
    used_at = models.DateTimeField(default=timezone.now)
