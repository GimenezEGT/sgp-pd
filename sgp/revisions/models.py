"""Revisão controlada dos modelos (feature 013; data-model.md).

`RevisableTemplate` acrescenta aos modelos de formulário (004) e de layout (006) os campos da
revisão; as etapas e as assinaturas ficam em tabelas somente de inclusão.
"""

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from sgp.core.models import AppendOnlyModel, ProtectedModel


class ReviewStatus(models.TextChoices):
    EDITING = "editing", "Em elaboração"
    SUBMITTED = "submitted", "Enviada para aprovação"


class RevisableTemplate(models.Model):
    review_status = models.CharField(
        "situação da revisão",
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.EDITING,
    )
    revision_reason = models.TextField("motivo da revisão", blank=True)
    revision_impact = models.TextField("impacto esperado", blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    discarded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    discarded_at = models.DateTimeField(null=True, blank=True)
    discard_reason = models.TextField("motivo do descarte", blank=True)
    approved_hash = models.CharField("resumo aprovado", max_length=64, blank=True)

    class Meta:
        abstract = True


class TemplateKind(models.TextChoices):
    FORM = "form", "Modelo de subdocumento"
    LAYOUT = "layout", "Modelo de layout"


class Step(models.TextChoices):
    OPENED = "opened", "Revisão aberta"
    SUBMITTED = "submitted", "Enviada para aprovação"
    RETURNED = "returned", "Devolvida"
    APPROVED = "approved", "Aprovada com assinatura"
    BECAME_CURRENT = "became_current", "Entrou em vigência"
    DISCARDED = "discarded", "Descartada"


class TemplateStep(AppendOnlyModel):
    kind = models.CharField(max_length=10, choices=TemplateKind.choices)
    template_id = models.PositiveBigIntegerField()
    version = models.PositiveSmallIntegerField()
    family = models.CharField(max_length=60)
    step = models.CharField(max_length=20, choices=Step.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    at = models.DateTimeField(default=timezone.now)
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ["at", "pk"]
        indexes = [models.Index(fields=["kind", "template_id"], name="revisions_step_template")]


class SignaturePurpose(models.TextChoices):
    APPROVAL = "approval", "Aprovação de revisão"
    RETIREMENT = "retirement", "Retirada de uso"


class TemplateSignature(AppendOnlyModel):
    kind = models.CharField(max_length=10, choices=TemplateKind.choices)
    template_id = models.PositiveBigIntegerField()
    version = models.PositiveSmallIntegerField()
    purpose = models.CharField(max_length=20, choices=SignaturePurpose.choices)
    content_hash = models.CharField(max_length=64)
    meaning = models.CharField(max_length=20, default="approved")
    signer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    signer_name = models.CharField(max_length=200)
    signer_title = models.CharField(max_length=200, blank=True)
    signed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["signed_at", "pk"]


class RetirementStatus(models.TextChoices):
    REQUESTED = "requested", "Pedida"
    APPROVED = "approved", "Aprovada"
    RETURNED = "returned", "Devolvida"


class TemplateRetirement(ProtectedModel):
    """Retirada de uso de um modelo de subdocumento (FR-015)."""

    subdocument_type = models.ForeignKey(
        "vocab.Term", on_delete=models.PROTECT, related_name="+", verbose_name="tipo"
    )
    status = models.CharField(
        max_length=20, choices=RetirementStatus.choices, default=RetirementStatus.REQUESTED
    )
    reason = models.TextField("motivo")
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    requested_at = models.DateTimeField(default=timezone.now)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    comment = models.TextField(blank=True)
    signature = models.ForeignKey(
        TemplateSignature, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )

    class Meta:
        ordering = ["-requested_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["subdocument_type"],
                condition=Q(status="requested"),
                name="revisions_one_open_retirement",
            )
        ]
