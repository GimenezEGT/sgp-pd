"""Formulário do modelo de layout: parâmetros editáveis sem programação (FR-019)."""

from decimal import Decimal

from django import forms

from .layout_schema import FONTS, VARIANTS

VARIANT_LABELS = {
    "": "padrão (tópicos)",
    "topics": "tópicos ('ESTE RELATÓRIO DEVE CONTER')",
    "checklist": "CHECK LIST na capa",
    "sectors": "tópicos e setores com caixas",
}

# (seção, chave, campo do formulário, rótulo, tipo, mínimo, máximo)
FIELDS = (
    ("page", "margin_top_cm", "margin_top_cm", "Margem superior (cm)", "number", 0.5, 4),
    ("page", "margin_bottom_cm", "margin_bottom_cm", "Margem inferior (cm)", "number", 0.5, 4),
    ("page", "margin_left_cm", "margin_left_cm", "Margem esquerda (cm)", "number", 0.5, 4),
    ("page", "margin_right_cm", "margin_right_cm", "Margem direita (cm)", "number", 0.5, 4),
    ("font", "family", "font_family", "Fonte", "font", None, None),
    ("font", "body_pt", "body_pt", "Tamanho do texto (pt)", "number", 6, 40),
    ("logo", "width_cm", "logo_width_cm", "Largura do logotipo (cm)", "number", 2, 18),
    ("logo", "height_cm", "logo_height_cm", "Altura do logotipo (cm)", "number", 0.5, 5),
    ("cover", "indent_cm", "cover_indent_cm", "Recuo do conteúdo da capa (cm)", "number", 0, 8),
    (
        "cover",
        "second_column_cm",
        "cover_second_column_cm",
        "Distância da 2ª coluna de tópicos (cm)",
        "number",
        2,
        12,
    ),
    ("cover", "title_pt", "cover_title_pt", "Título (pt)", "number", 6, 40),
    ("cover", "product_pt", "cover_product_pt", "Nome do produto (pt)", "number", 6, 40),
    ("cover", "version_pt", "cover_version_pt", "Versão (pt)", "number", 6, 40),
    (
        "cover",
        "contains_pt",
        "cover_contains_pt",
        "'ESTE RELATÓRIO DEVE CONTER' (pt)",
        "number",
        6,
        40,
    ),
    ("cover", "topics_pt", "cover_topics_pt", "Tópicos da capa (pt)", "number", 6, 40),
    ("cover", "signature_pt", "cover_signature_pt", "Bloco de assinaturas (pt)", "number", 6, 40),
    (
        "cover",
        "checklist_header_pt",
        "cover_checklist_header_pt",
        "Cabeçalho da CHECK LIST (pt)",
        "number",
        6,
        40,
    ),
    ("header", "text", "header_text", "Texto do cabeçalho", "text", None, None),
    ("header", "pt", "header_pt", "Cabeçalho (pt)", "number", 6, 40),
    ("footer", "text", "footer_text", "Texto adicional do rodapé", "text", None, None),
    ("footer", "pt", "footer_pt", "Rodapé (pt)", "number", 6, 40),
    ("body", "heading_pt", "body_heading_pt", "Títulos de tópico (pt)", "number", 6, 40),
    ("body", "table_pt", "body_table_pt", "Texto das tabelas (pt)", "number", 6, 40),
    (
        "body",
        "table_header_fill",
        "body_table_header_fill",
        "Cor do cabeçalho das tabelas",
        "color",
        None,
        None,
    ),
    ("watermark", "text", "watermark_text", "Texto da marca d'água", "text", None, None),
    ("watermark", "pt", "watermark_pt", "Marca d'água (pt)", "number", 20, 120),
    ("watermark", "color", "watermark_color", "Cor da marca d'água", "color", None, None),
)
SECTIONS = (
    (
        "Página e fonte",
        (
            "margin_top_cm",
            "margin_bottom_cm",
            "margin_left_cm",
            "margin_right_cm",
            "font_family",
            "body_pt",
        ),
    ),
    ("Logotipo", ("logo_width_cm", "logo_height_cm", "logo")),
    (
        "Capa",
        (
            "cover_indent_cm",
            "cover_second_column_cm",
            "cover_title_pt",
            "cover_product_pt",
            "cover_version_pt",
            "cover_contains_pt",
            "cover_topics_pt",
            "cover_signature_pt",
            "cover_checklist_header_pt",
        ),
    ),
    ("Cabeçalho e rodapé", ("header_text", "header_pt", "footer_text", "footer_pt")),
    ("Corpo", ("body_heading_pt", "body_table_pt", "body_table_header_fill")),
    ("Marca d'água", ("watermark_text", "watermark_pt", "watermark_color")),
)


def _plain(value):
    value = Decimal(value)
    return int(value) if value == value.to_integral_value() else float(value)


class LayoutForm(forms.Form):
    valid_from = forms.DateField(
        label="Início de vigência", widget=forms.DateInput(attrs={"type": "date"})
    )
    row_version = forms.IntegerField(widget=forms.HiddenInput)
    logo = forms.FileField(
        label="Novo logotipo (PNG ou JPEG)",
        required=False,
        help_text="Deixe em branco para manter o logotipo atual.",
    )

    def __init__(self, *args, type_terms=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.type_terms = list(type_terms)
        for _section, _key, name, label, kind, minimum, maximum in FIELDS:
            if kind == "number":
                self.fields[name] = forms.DecimalField(
                    label=label, min_value=minimum, max_value=maximum, decimal_places=2
                )
            elif kind == "font":
                self.fields[name] = forms.ChoiceField(
                    label=label, choices=[(font, font) for font in FONTS]
                )
            elif kind == "color":
                self.fields[name] = forms.RegexField(
                    label=label,
                    regex=r"^#[0-9A-Fa-f]{6}$",
                    widget=forms.TextInput(attrs={"type": "color"}),
                    error_messages={"invalid": "Use a cor no formato #RRGGBB."},
                )
            else:
                self.fields[name] = forms.CharField(
                    label=label,
                    required=name == "watermark_text",
                    max_length=60 if name == "watermark_text" else 300,
                    help_text="Marcadores: {titulo}, {produto}, {versao}, {projeto}."
                    if name in ("header_text", "footer_text")
                    else "",
                )
        for term in self.type_terms:
            self.fields[f"title_pt__{term.code}"] = forms.DecimalField(
                label=f"Título de {term.label} (pt)",
                required=False,
                min_value=6,
                max_value=40,
                decimal_places=2,
                help_text="Em branco: usa o tamanho geral do título.",
            )
            self.fields[f"topics_pt__{term.code}"] = forms.DecimalField(
                label=f"Tópicos da capa de {term.label} (pt)",
                required=False,
                min_value=6,
                max_value=40,
                decimal_places=2,
                help_text="Em branco: usa o tamanho geral dos tópicos.",
            )
            self.fields[f"variant__{term.code}"] = forms.ChoiceField(
                label=f"Capa de {term.label}",
                required=False,
                choices=[(value, VARIANT_LABELS[value]) for value in ("", *VARIANTS)],
            )

    @classmethod
    def initial_from(cls, layout) -> dict:
        definition = layout.definition
        initial = {"valid_from": layout.valid_from, "row_version": layout.row_version}
        for section, key, name, *_rest in FIELDS:
            initial[name] = definition[section][key]
        for code, size in definition["cover"].get("title_pt_by_type", {}).items():
            initial[f"title_pt__{code}"] = size
        for code, variant in definition["cover"].get("variant_by_type", {}).items():
            initial[f"variant__{code}"] = variant
        for code, size in definition["cover"].get("topics_pt_by_type", {}).items():
            initial[f"topics_pt__{code}"] = size
        return initial

    def definition(self) -> dict:
        data = self.cleaned_data
        definition = {section: {} for section, *_ in FIELDS}
        for section, key, name, _label, kind, *_ in FIELDS:
            value = data[name]
            definition[section][key] = _plain(value) if kind == "number" else (value or "")
        definition["body"]["table_header_fill"] = definition["body"]["table_header_fill"].upper()
        definition["watermark"]["color"] = definition["watermark"]["color"].upper()
        definition["cover"]["title_pt_by_type"] = {
            term.code: _plain(data[f"title_pt__{term.code}"])
            for term in self.type_terms
            if data.get(f"title_pt__{term.code}") is not None
        }
        definition["cover"]["variant_by_type"] = {
            term.code: data[f"variant__{term.code}"]
            for term in self.type_terms
            if data.get(f"variant__{term.code}")
        }
        definition["cover"]["topics_pt_by_type"] = {
            term.code: _plain(data[f"topics_pt__{term.code}"])
            for term in self.type_terms
            if data.get(f"topics_pt__{term.code}") is not None
        }
        return definition

    def sections(self):
        for title, names in SECTIONS:
            yield title, [self[name] for name in names]
        if self.type_terms:
            names = []
            for term in self.type_terms:
                names += [
                    f"title_pt__{term.code}",
                    f"topics_pt__{term.code}",
                    f"variant__{term.code}",
                ]
            yield "Por tipo de subdocumento", [self[name] for name in names]
