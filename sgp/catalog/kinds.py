"""Registro dos tipos de cadastro usado pelas telas genéricas e pelo versionamento (research R7).

Cada tipo informa o slug da URL, o modelo, os campos editáveis, as colunas da lista, os campos
de busca, o campo de código que congela no bloqueio (FR-004) e as chaves de unicidade entre os
vigentes.
"""

from dataclasses import dataclass, field

from django.http import Http404

from sgp.core.formatting import local_date

from .models import (
    BibliographicReference,
    Lot,
    Material,
    Panel,
    ReferenceKit,
    Sample,
    Standard,
    month_year,
)


@dataclass(frozen=True)
class Kind:
    slug: str
    model: type
    label: str
    label_plural: str
    description: str
    fields: tuple[str, ...]
    search_fields: tuple[str, ...]
    columns: tuple[tuple[str, str], ...]
    unique_together: tuple[str, ...] = ()
    code_field: str | None = None
    project_scoped: bool = False
    has_samples: bool = False
    month_fields: tuple[str, ...] = field(default_factory=tuple)

    @property
    def object_type(self) -> str:
        return f"{self.model._meta.app_label}.{self.model._meta.model_name}"


KINDS: dict[str, Kind] = {}


def register(kind: Kind) -> Kind:
    KINDS[kind.slug] = kind
    return kind


LOTS = register(
    Kind(
        slug="lotes",
        model=Lot,
        label="Lote",
        label_plural="Lotes",
        description="Lotes piloto, de validação e de produção de cada projeto.",
        fields=(
            "project",
            "code",
            "lot_type",
            "manufacture_date",
            "expiry_date",
            "manufacturing_site",
            "production_responsible",
        ),
        search_fields=("code",),
        columns=(
            ("Lote", "display"),
            ("Tipo", "get_lot_type_display"),
            ("Projeto", "project"),
            ("Local de fabricação", "manufacturing_site"),
        ),
        unique_together=("project", "code"),
        code_field="code",
        project_scoped=True,
        month_fields=("manufacture_date", "expiry_date"),
    )
)
MATERIALS = register(
    Kind(
        slug="insumos",
        model=Material,
        label="Insumo",
        label_plural="Insumos",
        description="Matérias-primas e materiais de embalagem, com certificado de análise.",
        fields=(
            "code",
            "description",
            "material_type",
            "manufacturer",
            "manufacturer_lot",
            "certificate",
            "certificate_valid_until",
            "new_to_company",
        ),
        search_fields=("code", "description"),
        columns=(
            ("Código", "code"),
            ("Descrição", "description"),
            ("Tipo", "get_material_type_display"),
            ("Fabricante", "manufacturer"),
        ),
        unique_together=("code",),
        code_field="code",
    )
)
REFERENCE_KITS = register(
    Kind(
        slug="kits",
        model=ReferenceKit,
        label="Kit de referência",
        label_plural="Kits de referência",
        description="Kits de referência e comparativos usados nos estudos.",
        fields=("name", "manufacturer", "lot", "expiry_date", "registration_number"),
        search_fields=("name", "manufacturer", "lot"),
        columns=(
            ("Kit", "name"),
            ("Fabricante", "manufacturer"),
            ("Lote", "lot"),
            ("Registro", "registration_number"),
        ),
        month_fields=("expiry_date",),
    )
)
SAMPLES = register(
    Kind(
        slug="amostras",
        model=Sample,
        label="Amostra",
        label_plural="Amostras",
        description="Amostras identificadas só pelo código interno, sem dados de pacientes.",
        fields=(
            "identifier",
            "sample_type",
            "origin",
            "characterization",
            "storage",
            "storage_detail",
            "collection_date",
        ),
        search_fields=("identifier", "origin"),
        columns=(
            ("Identificador", "identifier"),
            ("Tipo", "sample_type"),
            ("Origem", "origin"),
            ("Armazenamento", "storage"),
        ),
        unique_together=("identifier",),
    )
)
PANELS = register(
    Kind(
        slug="paineis",
        model=Panel,
        label="Painel",
        label_plural="Painéis",
        description="Conjuntos de amostras, cada uma numa versão definida.",
        fields=("code", "description"),
        search_fields=("code", "description"),
        columns=(("Código", "code"), ("Descrição", "description")),
        unique_together=("code",),
        has_samples=True,
    )
)
STANDARDS = register(
    Kind(
        slug="normas",
        model=Standard,
        label="Norma",
        label_plural="Normas",
        description="Biblioteca de normas técnicas reutilizáveis entre projetos.",
        fields=("identifier", "title", "scope"),
        search_fields=("identifier", "title"),
        columns=(
            ("Identificação", "identifier"),
            ("Título", "title"),
            ("Abrangência", "get_scope_display"),
        ),
        unique_together=("identifier",),
    )
)
REFERENCES = register(
    Kind(
        slug="referencias",
        model=BibliographicReference,
        label="Referência bibliográfica",
        label_plural="Referências bibliográficas",
        description="Biblioteca de referências bibliográficas reutilizáveis.",
        fields=("citation", "year", "doi_or_url"),
        search_fields=("citation", "doi_or_url"),
        columns=(("Citação", "__str__"), ("Ano", "year"), ("DOI ou endereço", "doi_or_url")),
    )
)


def get_kind(slug: str) -> Kind:
    try:
        return KINDS[slug]
    except KeyError:
        raise Http404("Tipo de cadastro inexistente.") from None


def kind_for(record) -> Kind:
    for kind in KINDS.values():
        if isinstance(record, kind.model):
            return kind
    raise LookupError(f"Modelo sem tipo de cadastro: {type(record).__name__}")


def value_of(record, accessor: str):
    value = getattr(record, accessor)
    return value() if callable(value) else value


def _presentable(record, kind: Kind, name: str) -> str:
    model_field = record._meta.get_field(name)
    value = getattr(record, name)
    if value is None or value == "":
        return "—"
    if model_field.choices:
        return getattr(record, f"get_{name}_display")()
    if isinstance(value, bool):
        return "Sim" if value else "Não"
    if name in kind.month_fields:
        return month_year(value)
    if hasattr(value, "strftime"):
        return local_date(value)
    if model_field.is_relation:
        full_name = getattr(value, "get_full_name", None)
        return full_name() if callable(full_name) else str(value)
    return str(value)


def display_rows(record) -> list[dict]:
    """Rótulo e valor de cada campo para o detalhe do cadastro."""
    kind = kind_for(record)
    rows = []
    for name in kind.fields:
        model_field = record._meta.get_field(name)
        row = {
            "label": str(model_field.verbose_name).capitalize(),
            "value": _presentable(record, kind, name),
            "file": None,
        }
        if name == "certificate" and record.certificate_id:
            row["file"] = record.certificate
        rows.append(row)
    return rows
