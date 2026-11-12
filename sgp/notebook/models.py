"""Caderno de laboratório eletrônico (data-model.md da feature 008).

Entradas e modelos são protegidos contra exclusão; adendos e assinaturas são somente de inclusão.
Materiais, anexos e vínculos saem por retirada lógica (quem e quando), nunca apagados.
"""

import uuid

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils import timezone

from sgp.core.models import AppendOnlyModel, ProtectedModel

USER = settings.AUTH_USER_MODEL
TEXT_FIELDS = ("objective", "hypothesis", "procedure", "results", "conclusion")
TEXT_LABELS = {
    "objective": "Objetivo",
    "hypothesis": "Hipótese",
    "procedure": "Procedimento",
    "results": "Resultados",
    "conclusion": "Conclusão",
}


def _search_vector():
    return models.GeneratedField(
        expression=SearchVector("search_text", config="portuguese"),
        output_field=SearchVectorField(),
        db_persist=True,
    )


class EntryStatus(models.TextChoices):
    OPEN = "open", "Aberta"
    SIGNED = "signed", "Assinada"
    WITNESSED = "witnessed", "Testemunhada"


class EntryTemplate(ProtectedModel):
    lineage = models.UUIDField("linhagem", default=uuid.uuid4, editable=False, db_index=True)
    version = models.PositiveIntegerField("versão", default=1)
    is_current = models.BooleanField("vigente", default=True)
    active = models.BooleanField("ativo", default=True)
    name = models.CharField("tipo de experimento", max_length=200)
    objective = models.TextField("objetivo", blank=True)
    hypothesis = models.TextField("hipótese", blank=True)
    procedure = models.TextField("procedimento", blank=True)
    results = models.TextField("resultados", blank=True)
    conclusion = models.TextField("conclusão", blank=True)
    change_reason = models.CharField("motivo da alteração", max_length=500, blank=True)
    created_by = models.ForeignKey(USER, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField("criado em", default=timezone.now)

    class Meta:
        verbose_name = "modelo de entrada"
        verbose_name_plural = "modelos de entrada"
        ordering = ["name", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["lineage", "version"], name="notebook_template_version_unique"
            ),
            models.UniqueConstraint(
                Lower("name"),
                condition=Q(is_current=True),
                name="notebook_template_current_name_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} (versão {self.version})"


class NotebookEntry(ProtectedModel):
    project = models.ForeignKey(
        "projects.Project", on_delete=models.PROTECT, related_name="notebook_entries"
    )
    number = models.PositiveIntegerField("número")
    author = models.ForeignKey(USER, on_delete=models.PROTECT, related_name="notebook_entries")
    created_at = models.DateTimeField("criada em", default=timezone.now)
    title = models.CharField("título", max_length=300)
    objective = models.TextField("objetivo", blank=True)
    hypothesis = models.TextField("hipótese", blank=True)
    procedure = models.TextField("procedimento", blank=True)
    results = models.TextField("resultados", blank=True)
    conclusion = models.TextField("conclusão", blank=True)
    template = models.ForeignKey(
        EntryTemplate,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="entries",
        verbose_name="modelo usado",
    )
    relevant = models.BooleanField("relevante (exige testemunha)", default=False)
    relevant_by = models.ForeignKey(
        USER, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    relevant_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        "situação", max_length=12, choices=EntryStatus.choices, default=EntryStatus.OPEN
    )
    signed_at = models.DateTimeField("assinada em", null=True, blank=True)
    witnessed_at = models.DateTimeField("testemunhada em", null=True, blank=True)
    search_text = models.TextField(default="", blank=True)
    search_vector = _search_vector()
    updated_by = models.ForeignKey(USER, on_delete=models.PROTECT, related_name="+")
    updated_at = models.DateTimeField(default=timezone.now)
    row_version = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "entrada do caderno"
        verbose_name_plural = "entradas do caderno"
        ordering = ["-created_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "number"], name="notebook_entry_number_unique"
            ),
        ]
        indexes = [
            GinIndex(fields=["search_vector"], name="notebook_entry_search_idx"),
            models.Index(fields=["project", "-created_at"], name="notebook_entry_timeline_idx"),
            models.Index(
                fields=["project", "status", "created_at"], name="notebook_entry_pending_idx"
            ),
        ]

    def __str__(self) -> str:
        code = self.project.code or "sem código"
        return f"Entrada {self.number} do caderno {code} – {self.title}"

    @property
    def is_open(self) -> bool:
        return self.status == EntryStatus.OPEN


class MaterialKind(models.TextChoices):
    LOT = "lot", "Lote"
    MATERIAL = "material", "Insumo"
    SAMPLE = "sample", "Amostra"


class EntryMaterial(ProtectedModel):
    entry = models.ForeignKey(NotebookEntry, on_delete=models.PROTECT, related_name="materials")
    kind = models.CharField("tipo", max_length=10, choices=MaterialKind.choices)
    lot = models.ForeignKey(
        "catalog.Lot", on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    material = models.ForeignKey(
        "catalog.Material", on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    sample = models.ForeignKey(
        "catalog.Sample", on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    code = models.CharField("código", max_length=100)
    version = models.PositiveIntegerField("versão do cadastro")
    added_by = models.ForeignKey(USER, on_delete=models.PROTECT, related_name="+")
    added_at = models.DateTimeField(default=timezone.now)
    removed_by = models.ForeignKey(
        USER, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    removed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "material da entrada"
        verbose_name_plural = "materiais da entrada"
        ordering = ["pk"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(
                        kind="lot",
                        lot__isnull=False,
                        material__isnull=True,
                        sample__isnull=True,
                    )
                    | Q(
                        kind="material",
                        lot__isnull=True,
                        material__isnull=False,
                        sample__isnull=True,
                    )
                    | Q(
                        kind="sample",
                        lot__isnull=True,
                        material__isnull=True,
                        sample__isnull=False,
                    )
                ),
                name="notebook_material_one_record",
            ),
            models.UniqueConstraint(
                fields=["entry", "kind", "code"],
                condition=Q(removed_at__isnull=True),
                name="notebook_material_active_unique",
            ),
        ]

    @property
    def record(self):
        return self.lot or self.material or self.sample

    @property
    def record_id(self) -> int:
        return self.lot_id or self.material_id or self.sample_id


class EntryAttachment(ProtectedModel):
    entry = models.ForeignKey(NotebookEntry, on_delete=models.PROTECT, related_name="attachments")
    file = models.ForeignKey("files.StoredFile", on_delete=models.PROTECT, related_name="+")
    inline = models.BooleanField("imagem no texto", default=False)
    added_by = models.ForeignKey(USER, on_delete=models.PROTECT, related_name="+")
    added_at = models.DateTimeField(default=timezone.now)
    removed_by = models.ForeignKey(
        USER, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    removed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "anexo da entrada"
        verbose_name_plural = "anexos da entrada"
        ordering = ["pk"]

    @property
    def is_image(self) -> bool:
        return self.file.content_type in ("image/png", "image/jpeg")

    @property
    def is_spreadsheet(self) -> bool:
        return self.file.original_name.lower().endswith((".csv", ".xlsx"))


class Addendum(AppendOnlyModel):
    entry = models.ForeignKey(NotebookEntry, on_delete=models.PROTECT, related_name="addenda")
    number = models.PositiveIntegerField("número")
    text = models.TextField("texto")
    author = models.ForeignKey(USER, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField("criado em", default=timezone.now)
    content_hash = models.CharField("resumo SHA-256", max_length=64)
    search_text = models.TextField(default="", blank=True)
    search_vector = _search_vector()

    class Meta:
        verbose_name = "adendo"
        verbose_name_plural = "adendos"
        ordering = ["entry", "number"]
        constraints = [
            models.UniqueConstraint(fields=["entry", "number"], name="notebook_addendum_unique"),
        ]
        indexes = [GinIndex(fields=["search_vector"], name="notebook_addendum_search_idx")]


class SignatureRole(models.TextChoices):
    AUTHOR = "author", "Autor"
    WITNESS = "witness", "Testemunha"


class NotebookSignature(AppendOnlyModel):
    entry = models.ForeignKey(NotebookEntry, on_delete=models.PROTECT, related_name="signatures")
    addendum = models.ForeignKey(
        Addendum, on_delete=models.PROTECT, null=True, blank=True, related_name="signatures"
    )
    role = models.CharField("papel", max_length=10, choices=SignatureRole.choices)
    signer = models.ForeignKey(USER, on_delete=models.PROTECT, related_name="+")
    signed_at = models.DateTimeField("assinada em", default=timezone.now)
    content_hash = models.CharField("resumo SHA-256", max_length=64)

    class Meta:
        verbose_name = "assinatura do caderno"
        verbose_name_plural = "assinaturas do caderno"
        ordering = ["signed_at", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["entry", "role"],
                condition=Q(addendum__isnull=True),
                name="notebook_signature_entry_role_unique",
            ),
            models.UniqueConstraint(
                fields=["addendum"],
                condition=Q(addendum__isnull=False),
                name="notebook_signature_addendum_unique",
            ),
        ]


class LinkTarget(models.TextChoices):
    SUBDOCUMENT = "subdocument", "Subdocumento"
    LOT = "lot", "Lote"
    STUDY = "study", "Estudo"


class LinkKind(models.TextChoices):
    RELATED = "related", "Relacionado"
    PROMOTED = "promoted", "Dados promovidos"


class NotebookLink(ProtectedModel):
    entry = models.ForeignKey(NotebookEntry, on_delete=models.PROTECT, related_name="links")
    target_type = models.CharField("alvo", max_length=12, choices=LinkTarget.choices)
    subdocument = models.ForeignKey(
        "subdocuments.Subdocument",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="notebook_links",
    )
    lot = models.ForeignKey(
        "catalog.Lot",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="notebook_links",
    )
    study = models.ForeignKey(
        "studies.Study",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="notebook_links",
    )
    kind = models.CharField("tipo", max_length=10, choices=LinkKind.choices)
    attachment = models.ForeignKey(
        EntryAttachment,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="promotions",
    )
    created_by = models.ForeignKey(USER, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(default=timezone.now)
    removed_by = models.ForeignKey(
        USER, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    removed_at = models.DateTimeField(null=True, blank=True)
    removal_reason = models.CharField("motivo da retirada", max_length=500, blank=True)

    class Meta:
        verbose_name = "vínculo do caderno"
        verbose_name_plural = "vínculos do caderno"
        ordering = ["pk"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(
                        target_type="subdocument",
                        subdocument__isnull=False,
                        lot__isnull=True,
                        study__isnull=True,
                    )
                    | Q(
                        target_type="lot",
                        subdocument__isnull=True,
                        lot__isnull=False,
                        study__isnull=True,
                    )
                    | Q(
                        target_type="study",
                        subdocument__isnull=True,
                        lot__isnull=True,
                        study__isnull=False,
                    )
                ),
                name="notebook_link_one_target",
            ),
            models.CheckConstraint(
                condition=Q(kind="related", attachment__isnull=True)
                | Q(kind="promoted", target_type="study", attachment__isnull=False),
                name="notebook_link_promotion_origin",
            ),
            models.UniqueConstraint(
                fields=["entry", "target_type", "subdocument", "lot", "study"],
                condition=Q(removed_at__isnull=True, kind="related"),
                nulls_distinct=False,
                name="notebook_link_active_unique",
            ),
        ]

    @property
    def target(self):
        return self.subdocument or self.lot or self.study
