"""Estudos de desempenho e estabilidade (feature 007; data-model.md).

Cada versão é uma linha com a mesma linhagem; linhas, critérios e resultados ficam no estudo como
dados estruturados (como as tabelas dos subdocumentos). Nada é apagado fisicamente.
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from sgp.core.models import ProtectedModel


class StudyStatus(models.TextChoices):
    EDITING = "editing", "Em elaboração"
    LOCKED = "locked", "Bloqueado"


class Rounding(models.TextChoices):
    HALF_EVEN = "half_even", "Meio para o par"
    HALF_UP = "half_up", "Meio para cima"
    TRUNCATE = "truncate", "Truncar"


class CIMethod(models.TextChoices):
    CLOPPER_PEARSON = "clopper_pearson", "Exato de Clopper-Pearson"
    WILSON = "wilson", "Wilson"


class CutoffDirection(models.TextChoices):
    GE = "ge", "Positivo quando o valor é maior ou igual ao corte"
    LE = "le", "Positivo quando o valor é menor ou igual ao corte"


class Study(ProtectedModel):
    lineage = models.UUIDField(default=uuid.uuid4, editable=False)
    version = models.PositiveSmallIntegerField("versão", default=1)
    project = models.ForeignKey(
        "projects.Project", on_delete=models.PROTECT, related_name="studies"
    )
    study_type = models.ForeignKey(
        "vocab.Term", on_delete=models.PROTECT, related_name="+", verbose_name="tipo de estudo"
    )
    title = models.CharField("título", max_length=200)
    subdocument = models.ForeignKey(
        "subdocuments.Subdocument",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="studies",
    )
    topic_key = models.CharField("tópico", max_length=60, blank=True)
    status = models.CharField(
        max_length=20, choices=StudyStatus.choices, default=StudyStatus.EDITING
    )
    rounding = models.CharField(
        "arredondamento", max_length=20, choices=Rounding.choices, default=Rounding.HALF_EVEN
    )
    places = models.PositiveSmallIntegerField("casas decimais", default=2)
    fine_places = models.PositiveSmallIntegerField("casas de R², correlação e regressão", default=4)
    ci_method = models.CharField(
        "IC 95% de proporções",
        max_length=20,
        choices=CIMethod.choices,
        default=CIMethod.CLOPPER_PEARSON,
    )
    cutoff = models.DecimalField(
        "valor de corte", max_digits=18, decimal_places=6, null=True, blank=True
    )
    cutoff_direction = models.CharField(
        "interpretação do corte",
        max_length=2,
        choices=CutoffDirection.choices,
        default=CutoffDirection.GE,
    )
    criteria = models.JSONField("critérios de aceitação", default=list, blank=True)
    rows = models.JSONField("medidas", default=list, blank=True)
    results = models.JSONField("resultados calculados", default=dict, blank=True)
    not_applicable = models.BooleanField("não aplicável", default=False)
    justification = models.TextField("justificativa", blank=True)
    version_reason = models.TextField("motivo da versão", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    updated_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    locked_at = models.DateTimeField(null=True, blank=True)
    row_version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["project", "title", "-version"]
        constraints = [
            models.UniqueConstraint(fields=["lineage", "version"], name="studies_lineage_version")
        ]

    def __str__(self) -> str:
        return f"{self.title} – versão {self.version_display}"

    @property
    def version_display(self) -> str:
        return f"{self.version:02d}"

    @property
    def is_locked(self) -> bool:
        return self.status == StudyStatus.LOCKED

    @property
    def config(self) -> dict:
        return {
            "rounding": self.rounding,
            "places": self.places,
            "fine_places": self.fine_places,
            "ci_method": self.ci_method,
            "cutoff": str(self.cutoff) if self.cutoff is not None else None,
            "cutoff_direction": self.cutoff_direction,
        }


class ImportMapping(ProtectedModel):
    equipment = models.CharField("equipamento", max_length=120, unique=True)
    mapping = models.JSONField("mapeamento de colunas", default=dict)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["equipment"]

    def __str__(self) -> str:
        return self.equipment
