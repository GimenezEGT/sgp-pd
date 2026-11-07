"""Cadastros de apoio versionados (feature 003, research R1).

Cada linha é uma versão do cadastro. `lineage` identifica o mesmo cadastro ao longo das versões;
só uma versão é vigente (`is_current`). Referências de documentos apontam para a linha (a
versão), por isso a versão antiga continua mostrando o valor que foi usado.
"""

import uuid

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from sgp.core.models import ProtectedModel, ProtectedQuerySet


def month_year(value) -> str:
    return value.strftime("%m/%Y") if value else ""


class VersionedQuerySet(ProtectedQuerySet):
    def current(self):
        return self.filter(is_current=True)

    def available(self):
        """Vigentes e ativos: os que podem receber novas referências."""
        return self.filter(is_current=True, is_active=True)


class VersionedRecord(ProtectedModel):
    lineage = models.UUIDField("linhagem", default=uuid.uuid4, editable=False, db_index=True)
    version = models.PositiveIntegerField("versão", default=1)
    is_current = models.BooleanField("vigente", default=True)
    is_active = models.BooleanField("ativo", default=True)
    locked_at = models.DateTimeField("bloqueado em", null=True, blank=True)
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="bloqueado por",
    )
    lock_reason = models.CharField("motivo do bloqueio", max_length=300, blank=True)
    version_reason = models.TextField("motivo da versão", blank=True)
    row_version = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="criado por",
    )
    created_at = models.DateTimeField("criado em", default=timezone.now)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="alterado por",
    )
    updated_at = models.DateTimeField("alterado em", null=True, blank=True)

    objects = VersionedQuerySet.as_manager()

    class Meta:
        abstract = True
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["lineage", "version"], name="%(app_label)s_%(class)s_lineage_version"
            ),
            models.UniqueConstraint(
                fields=["lineage"],
                condition=Q(is_current=True),
                name="%(app_label)s_%(class)s_one_current",
            ),
        ]

    @property
    def is_locked(self) -> bool:
        return self.locked_at is not None

    @property
    def version_display(self) -> str:
        return f"{self.version:02d}"


# ------------------------------------------------------------------------ lotes


class LotType(models.TextChoices):
    PILOT = "pilot", "Piloto"
    VALIDATION = "validation", "Validação"
    PRODUCTION = "production", "Produção"


class Lot(VersionedRecord):
    project = models.ForeignKey(
        "projects.Project", on_delete=models.PROTECT, related_name="lots", verbose_name="projeto"
    )
    code = models.CharField("código", max_length=40)
    lot_type = models.CharField("tipo", max_length=20, choices=LotType.choices)
    manufacture_date = models.DateField("data de fabricação")
    expiry_date = models.DateField("validade")
    manufacturing_site = models.CharField("local de fabricação", max_length=200)
    production_responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="responsável pela produção",
    )

    class Meta(VersionedRecord.Meta):
        verbose_name = "lote"
        verbose_name_plural = "lotes"
        constraints = [
            *VersionedRecord.Meta.constraints,
            models.UniqueConstraint(
                fields=["project", "code"],
                condition=Q(is_current=True),
                name="catalog_lot_unique_code",
            ),
            models.CheckConstraint(
                condition=Q(expiry_date__gt=F("manufacture_date")),
                name="catalog_lot_expiry_after_manufacture",
            ),
        ]
        indexes = [GinIndex(fields=["code"], opclasses=["gin_trgm_ops"], name="catalog_lot_trgm")]

    def __str__(self) -> str:
        return self.display

    @property
    def display(self) -> str:
        """Formato único do lote em telas e documentos (FR-010)."""
        return (
            f"Lote {self.code} – Fabricação: {month_year(self.manufacture_date)} – "
            f"Validade: {month_year(self.expiry_date)}"
        )


# ---------------------------------------------------------------------- insumos


class MaterialType(models.TextChoices):
    RAW = "raw", "Matéria-prima"
    PACKAGING = "packaging", "Material de embalagem"


class Material(VersionedRecord):
    code = models.CharField("código", max_length=40)
    description = models.CharField("descrição", max_length=300)
    material_type = models.CharField("tipo", max_length=20, choices=MaterialType.choices)
    manufacturer = models.CharField("fabricante", max_length=200, blank=True)
    manufacturer_lot = models.CharField("lote do fabricante", max_length=100, blank=True)
    certificate = models.ForeignKey(
        "files.StoredFile",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="certificado de análise",
    )
    certificate_valid_until = models.DateField("validade do certificado", null=True, blank=True)
    new_to_company = models.BooleanField("novo para a empresa", default=False)

    class Meta(VersionedRecord.Meta):
        verbose_name = "insumo"
        verbose_name_plural = "insumos"
        constraints = [
            *VersionedRecord.Meta.constraints,
            models.UniqueConstraint(
                fields=["code"], condition=Q(is_current=True), name="catalog_material_unique_code"
            ),
        ]
        indexes = [
            GinIndex(
                fields=["code"], opclasses=["gin_trgm_ops"], name="catalog_material_code_trgm"
            ),
            GinIndex(
                fields=["description"],
                opclasses=["gin_trgm_ops"],
                name="catalog_material_desc_trgm",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} – {self.description}"

    @property
    def certificate_pending(self) -> bool:
        return self.certificate_id is None

    @property
    def certificate_expired(self) -> bool:
        valid_until = self.certificate_valid_until
        return bool(valid_until and valid_until < timezone.localdate())


# ------------------------------------------------------------ kits de referência


class ReferenceKit(VersionedRecord):
    name = models.CharField("nome", max_length=200)
    manufacturer = models.CharField("fabricante", max_length=200)
    lot = models.CharField("lote", max_length=100)
    expiry_date = models.DateField("validade")
    registration_number = models.CharField("número de registro", max_length=60, blank=True)

    class Meta(VersionedRecord.Meta):
        verbose_name = "kit de referência"
        verbose_name_plural = "kits de referência"
        indexes = [
            GinIndex(fields=["name"], opclasses=["gin_trgm_ops"], name="catalog_refkit_name_trgm")
        ]

    def __str__(self) -> str:
        return self.display

    @property
    def display(self) -> str:
        text = (
            f"{self.name} – {self.manufacturer} – Lote {self.lot} – "
            f"Validade: {month_year(self.expiry_date)}"
        )
        if self.registration_number:
            text += f" – Registro {self.registration_number}"
        return text


# --------------------------------------------------------------------- amostras


class Sample(VersionedRecord):
    """Amostra identificada só pelo código interno: nenhum dado pessoal (FR-015, FR-016)."""

    identifier = models.CharField("identificador interno", max_length=30)
    sample_type = models.ForeignKey(
        "vocab.Term",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="tipo de amostra",
    )
    origin = models.CharField("origem", max_length=200)
    characterization = models.TextField("caracterização")
    storage = models.ForeignKey(
        "vocab.Term",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="condição de armazenamento",
    )
    storage_detail = models.CharField("detalhe do armazenamento", max_length=200, blank=True)
    collection_date = models.DateField("data de coleta", null=True, blank=True)

    class Meta(VersionedRecord.Meta):
        verbose_name = "amostra"
        verbose_name_plural = "amostras"
        constraints = [
            *VersionedRecord.Meta.constraints,
            models.UniqueConstraint(
                fields=["identifier"],
                condition=Q(is_current=True),
                name="catalog_sample_unique_identifier",
            ),
        ]
        indexes = [
            GinIndex(
                fields=["identifier"], opclasses=["gin_trgm_ops"], name="catalog_sample_id_trgm"
            )
        ]

    def __str__(self) -> str:
        return f"Amostra {self.identifier}"


class Panel(VersionedRecord):
    code = models.CharField("código", max_length=40)
    description = models.CharField("descrição", max_length=300)

    class Meta(VersionedRecord.Meta):
        verbose_name = "painel"
        verbose_name_plural = "painéis"
        constraints = [
            *VersionedRecord.Meta.constraints,
            models.UniqueConstraint(
                fields=["code"], condition=Q(is_current=True), name="catalog_panel_unique_code"
            ),
        ]
        indexes = [
            GinIndex(fields=["code"], opclasses=["gin_trgm_ops"], name="catalog_panel_code_trgm"),
            GinIndex(
                fields=["description"], opclasses=["gin_trgm_ops"], name="catalog_panel_desc_trgm"
            ),
        ]

    def __str__(self) -> str:
        return f"Painel {self.code} – {self.description}"

    def active_links(self):
        return self.links.filter(removed_at__isnull=True).select_related(
            "sample", "sample__sample_type"
        )

    def samples(self) -> list[Sample]:
        return [link.sample for link in self.active_links()]


class PanelSample(ProtectedModel):
    """Vínculo do painel com uma versão de amostra; a retirada é marcada, nunca apagada."""

    panel = models.ForeignKey(Panel, on_delete=models.PROTECT, related_name="links")
    sample = models.ForeignKey(Sample, on_delete=models.PROTECT, related_name="panel_links")
    position = models.PositiveIntegerField("ordem", default=0)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    added_at = models.DateTimeField(default=timezone.now)
    removed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    removed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["position", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["panel", "sample"],
                condition=Q(removed_at__isnull=True),
                name="catalog_panelsample_unique_active",
            )
        ]


# ------------------------------------------------------------- normas e referências


class StandardScope(models.TextChoices):
    NATIONAL = "national", "Nacional"
    INTERNATIONAL = "international", "Internacional"


class Standard(VersionedRecord):
    identifier = models.CharField("identificação", max_length=100)
    title = models.CharField("título", max_length=300)
    scope = models.CharField("abrangência", max_length=20, choices=StandardScope.choices)

    class Meta(VersionedRecord.Meta):
        verbose_name = "norma"
        verbose_name_plural = "normas"
        constraints = [
            *VersionedRecord.Meta.constraints,
            models.UniqueConstraint(
                fields=["identifier"],
                condition=Q(is_current=True),
                name="catalog_standard_unique_identifier",
            ),
        ]
        indexes = [
            GinIndex(
                fields=["identifier"], opclasses=["gin_trgm_ops"], name="catalog_standard_id_trgm"
            ),
            GinIndex(
                fields=["title"], opclasses=["gin_trgm_ops"], name="catalog_standard_title_trgm"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.identifier} – {self.title}"


class BibliographicReference(VersionedRecord):
    citation = models.TextField("citação completa")
    year = models.PositiveSmallIntegerField("ano", null=True, blank=True)
    doi_or_url = models.CharField("DOI ou endereço", max_length=300, blank=True)

    class Meta(VersionedRecord.Meta):
        verbose_name = "referência bibliográfica"
        verbose_name_plural = "referências bibliográficas"
        indexes = [
            GinIndex(
                fields=["citation"], opclasses=["gin_trgm_ops"], name="catalog_reference_cit_trgm"
            )
        ]

    def __str__(self) -> str:
        text = " ".join(self.citation.split())
        return text if len(text) <= 120 else f"{text[:117]}..."


# ------------------------------------------------------------------- importação


class ImportStatus(models.TextChoices):
    PREVIEW = "preview", "Pré-visualizada (não confirmada)"
    CONFIRMED = "confirmed", "Confirmada"


class ImportBatch(ProtectedModel):
    """Importação de insumos: arquivo, resultado de cada linha e situação (FR-013)."""

    source_file = models.ForeignKey(
        "files.StoredFile", on_delete=models.PROTECT, related_name="+", verbose_name="arquivo"
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    uploaded_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        "situação", max_length=20, choices=ImportStatus.choices, default=ImportStatus.PREVIEW
    )
    rows = models.JSONField("linhas", default=list)
    valid_count = models.PositiveIntegerField(default=0)
    rejected_count = models.PositiveIntegerField(default=0)
    created_count = models.PositiveIntegerField(default=0)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        verbose_name = "importação de insumos"
        verbose_name_plural = "importações de insumos"
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return f"Importação {self.pk} – {self.source_file.original_name}"

    @property
    def total_count(self) -> int:
        return len(self.rows)

    def rejected_rows(self) -> list[dict]:
        return [row for row in self.rows if row.get("erros")]
