"""Dossiê técnico para a ANVISA (data-model.md da feature 011)."""

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from sgp.core.models import AppendOnlyModel, ProtectedModel

USER = settings.AUTH_USER_MODEL


class DossierDefinition(AppendOnlyModel):
    version = models.PositiveIntegerField("versão", unique=True)
    yaml = models.TextField("definição (YAML)")
    parsed = models.JSONField("definição normalizada")
    note = models.CharField("observação", max_length=500, blank=True)
    created_by = models.ForeignKey(USER, on_delete=models.PROTECT, null=True, related_name="+")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-version"]

    def __str__(self) -> str:
        return f"Definição do dossiê – versão {self.version}"


class TextStatus(models.TextChoices):
    DRAFT = "draft", "Em elaboração"
    APPROVED = "approved", "Aprovado"
    SUPERSEDED = "superseded", "Substituído"


class StandardText(ProtectedModel):
    key = models.SlugField("chave", max_length=80)
    lineage = models.UUIDField(default=uuid.uuid4, db_index=True)
    version = models.PositiveIntegerField("versão", default=1)
    title = models.CharField("título", max_length=200)
    text = models.TextField("texto")
    status = models.CharField(max_length=12, choices=TextStatus.choices, default=TextStatus.DRAFT)
    created_by = models.ForeignKey(USER, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(default=timezone.now)
    approved_by = models.ForeignKey(
        USER, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["key", "-version"]
        constraints = [
            models.UniqueConstraint(fields=["key", "version"], name="dossier_text_version_unique"),
            models.UniqueConstraint(
                fields=["key"],
                condition=Q(status="approved"),
                name="dossier_text_one_approved",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.title} – versão {self.version}"


COMPANY_DEFAULTS = {
    "legal_name": "",
    "city": "",
    "rt_name": "",
    "rt_council": "Conselho Regional de Farmácia",
    "rt_uf": "",
    "rt_number": "",
    "rt_title": "",
}


class CompanyProfile(ProtectedModel):
    legal_name = models.CharField("razão social", max_length=200)
    city = models.CharField("cidade", max_length=120)
    rt_name = models.CharField("responsável técnico e legal", max_length=200)
    rt_council = models.CharField(
        "conselho", max_length=120, default="Conselho Regional de Farmácia"
    )
    rt_uf = models.CharField("UF do conselho", max_length=2)
    rt_number = models.CharField("número no conselho", max_length=40)
    rt_title = models.CharField("cargo", max_length=120, blank=True)
    updated_by = models.ForeignKey(USER, on_delete=models.PROTECT, related_name="+")
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return self.legal_name


class DossierSupplement(ProtectedModel):
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="+")
    item_key = models.CharField("item", max_length=40)
    text = models.TextField("texto", blank=True)
    not_applicable = models.BooleanField("não aplicável", default=False)
    justification = models.TextField("justificativa", blank=True)
    updated_by = models.ForeignKey(USER, on_delete=models.PROTECT, related_name="+")
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "item_key"], name="dossier_supplement_unique"
            )
        ]

    def __str__(self) -> str:
        return f"Complemento {self.item_key} – {self.project}"


class DossierVersion(AppendOnlyModel):
    subject = models.CharField("projeto ou família", max_length=300, db_index=True)
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="+")
    number = models.PositiveIntegerField("versão")
    definition = models.ForeignKey(DossierDefinition, on_delete=models.PROTECT, related_name="+")
    risk_class = models.CharField("classe de risco", max_length=4, blank=True)
    final = models.BooleanField("final", default=False)
    checklist = models.JSONField("checagem")
    content = models.JSONField("conteúdo por item")
    content_hash = models.CharField(max_length=64)
    texts_used = models.JSONField(default=dict)
    sources = models.JSONField(default=dict)
    pdf = models.ForeignKey(
        "files.StoredFile", on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    docx = models.ForeignKey(
        "files.StoredFile", on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    package = models.ForeignKey(
        "files.StoredFile", on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    generated_by = models.ForeignKey(USER, on_delete=models.PROTECT, related_name="+")
    generated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-generated_at", "-pk"]
        constraints = [
            models.UniqueConstraint(fields=["subject", "number"], name="dossier_version_unique")
        ]

    def __str__(self) -> str:
        kind = "final" if self.final else "rascunho"
        return f"Dossiê {self.subject} – versão {self.number:02d} ({kind})"


class SubmissionResult(models.TextChoices):
    PENDING = "pending", "Aguardando resultado"
    GRANTED = "granted", "Deferido"
    REJECTED = "rejected", "Indeferido"
    REQUIREMENT = "requirement", "Exigência"


class Submission(ProtectedModel):
    version = models.ForeignKey(
        DossierVersion, on_delete=models.PROTECT, related_name="submissions"
    )
    protocol = models.CharField("processo ou expediente", max_length=80)
    submitted_on = models.DateField("data do envio")
    signed_pdf = models.ForeignKey(
        "files.StoredFile", on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    result = models.CharField(
        max_length=12, choices=SubmissionResult.choices, default=SubmissionResult.PENDING
    )
    result_on = models.DateField("data do resultado", null=True, blank=True)
    notes = models.TextField("observações", blank=True)
    created_by = models.ForeignKey(USER, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(default=timezone.now)
    updated_by = models.ForeignKey(USER, on_delete=models.PROTECT, related_name="+")
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-submitted_on", "-pk"]

    def __str__(self) -> str:
        return f"Envio {self.protocol} – {self.version}"
