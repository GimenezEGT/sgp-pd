"""Formulários dos cadastros, da importação e da mudança de situação (feature 003)."""

import re

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from sgp.accounts.models import User
from sgp.files.storage import DOCUMENT_KINDS, SPREADSHEET_KINDS, check_upload
from sgp.projects.models import Project
from sgp.vocab.models import Term

from . import lgpd
from .models import (
    BibliographicReference,
    Lot,
    Material,
    Panel,
    ReferenceKit,
    Sample,
    Standard,
)
from .permissions import lot_projects

SAMPLE_TYPE = "tipo-amostra"
STORAGE = "armazenamento"


class CatalogForm(forms.ModelForm):
    """Base: controle otimista (row_version) e motivo, obrigatório quando a versão está bloqueada."""

    row_version = forms.IntegerField(widget=forms.HiddenInput, required=False)
    reason = forms.CharField(
        label="Motivo da correção",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        help_text="Obrigatório quando o cadastro já foi usado em documento assinado.",
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field, forms.DateField):
                field.widget = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
                field.widget.is_required = field.required
        if self.instance.pk:
            self.fields["row_version"].initial = self.instance.row_version
            if self.instance.is_locked:
                self.fields["reason"].required = True
                self.fields["reason"].help_text = (
                    "Este cadastro já foi usado em documento assinado: a correção cria uma nova "
                    "versão e a anterior continua como está."
                )
        else:
            del self.fields["reason"]

    def model_data(self) -> dict:
        return {
            name: self.cleaned_data[name] for name in self._meta.fields if name in self.cleaned_data
        }

    def validate_unique(self):
        """A unicidade entre os vigentes é conferida pelo serviço de versões."""

    def _post_clean(self):
        # Os campos ficam no instance só pelo serviço; aqui só as validações de campo.
        pass


class LotForm(CatalogForm):
    class Meta:
        model = Lot
        fields = [
            "project",
            "code",
            "lot_type",
            "manufacture_date",
            "expiry_date",
            "manufacturing_site",
            "production_responsible",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["project"].queryset = (
            lot_projects(self.user) if self.user else Project.objects.none()
        )
        self.fields["project"].label_from_instance = lambda project: (
            f"{project.code} – {project.title}" if project.code else project.title
        )
        self.fields["production_responsible"].queryset = User.objects.filter(
            is_active=True
        ).order_by("full_name", "username")
        self.fields["production_responsible"].label_from_instance = lambda person: (
            person.get_full_name() or person.username
        )
        self.fields["code"].help_text = "Sem espaços; único entre os lotes vigentes do projeto."
        if self.instance.pk:
            self.fields["project"].disabled = True
            self.fields["project"].queryset = Project.objects.filter(pk=self.instance.project_id)

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip()
        if not re.fullmatch(settings.LOT_CODE_PATTERN, code):
            raise ValidationError(
                "Código de lote fora do padrão: use letras, números, hífen, barra ou ponto, sem "
                "espaços."
            )
        return code

    def clean(self):
        data = super().clean()
        made, expiry = data.get("manufacture_date"), data.get("expiry_date")
        if made and expiry and expiry <= made:
            self.add_error("expiry_date", "A validade precisa ser posterior à data de fabricação.")
        return data


class MaterialForm(CatalogForm):
    certificate_file = forms.FileField(
        label="Certificado de análise",
        required=False,
        help_text="PDF, PNG ou JPEG. Substitui o certificado atual, se houver.",
    )

    class Meta:
        model = Material
        fields = [
            "code",
            "description",
            "material_type",
            "manufacturer",
            "manufacturer_lot",
            "certificate_valid_until",
            "new_to_company",
        ]

    field_order = [
        "code",
        "description",
        "material_type",
        "manufacturer",
        "manufacturer_lot",
        "certificate_file",
        "certificate_valid_until",
        "new_to_company",
    ]

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip()
        if any(char.isspace() for char in code):
            raise ValidationError("O código do insumo não pode ter espaços.")
        return code

    def clean_certificate_file(self):
        uploaded = self.cleaned_data.get("certificate_file")
        if uploaded:
            check_upload(uploaded, DOCUMENT_KINDS)
        return uploaded

    def clean(self):
        data = super().clean()
        has_certificate = bool(data.get("certificate_file")) or bool(
            self.instance.pk and self.instance.certificate_id
        )
        if has_certificate and not data.get("certificate_valid_until"):
            self.add_error(
                "certificate_valid_until", "Informe a validade do certificado de análise."
            )
        return data


class ReferenceKitForm(CatalogForm):
    class Meta:
        model = ReferenceKit
        fields = ["name", "manufacturer", "lot", "expiry_date", "registration_number"]


def _terms_with_current(vocabulary: str, current_id):
    queryset = Term.objects.of(vocabulary)
    if current_id:
        return queryset.filter(is_active=True) | queryset.filter(pk=current_id)
    return queryset.filter(is_active=True)


class SampleForm(CatalogForm):
    class Meta:
        model = Sample
        fields = [
            "identifier",
            "sample_type",
            "origin",
            "characterization",
            "storage",
            "storage_detail",
            "collection_date",
        ]
        widgets = {"characterization": forms.Textarea(attrs={"rows": 3})}
        help_texts = {
            "identifier": "Código interno, sem espaços e com ao menos um dígito. Nunca o nome do paciente.",
            "origin": "Instituição ou banco de amostras, sem identificar o paciente.",
            "characterization": "Dados analíticos: resultado de referência, concentração, status.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance
        self.fields["sample_type"].queryset = _terms_with_current(
            SAMPLE_TYPE, instance.sample_type_id if instance.pk else None
        )
        self.fields["storage"].queryset = _terms_with_current(
            STORAGE, instance.storage_id if instance.pk else None
        )

    def clean_identifier(self):
        identifier = (self.cleaned_data.get("identifier") or "").strip()
        lgpd.validate_identifier(identifier)
        return identifier

    def _clean_text(self, name):
        value = self.cleaned_data.get(name) or ""
        lgpd.validate_no_personal_data(value)
        return value

    def clean_origin(self):
        return self._clean_text("origin")

    def clean_characterization(self):
        return self._clean_text("characterization")

    def clean_storage_detail(self):
        return self._clean_text("storage_detail")

    def clean_collection_date(self):
        value = self.cleaned_data.get("collection_date")
        if value and value > timezone.localdate():
            raise ValidationError("A data de coleta não pode estar no futuro.")
        return value


class SampleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, sample):
        text = f"{sample.identifier} (versão {sample.version_display}) – {sample.sample_type}"
        if not sample.is_current:
            text += " – versão substituída"
        if not sample.is_active:
            text += " – desativada"
        return text


class PanelForm(CatalogForm):
    samples = SampleChoiceField(
        label="Amostras",
        queryset=Sample.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Amostras vigentes e ativas, mais as versões que o painel já referencia.",
    )

    class Meta:
        model = Panel
        fields = ["code", "description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        available = Sample.objects.available()
        if self.instance.pk:
            linked_ids = [sample.pk for sample in self.instance.samples()]
            self.fields["samples"].queryset = (
                (Sample.objects.filter(pk__in=linked_ids) | available)
                .select_related("sample_type")
                .order_by("identifier", "-version")
            )
            self.fields["samples"].initial = linked_ids
        else:
            self.fields["samples"].queryset = available.select_related("sample_type").order_by(
                "identifier"
            )

    def clean_samples(self):
        samples = list(self.cleaned_data.get("samples") or [])
        lineages = [sample.lineage for sample in samples]
        if len(lineages) != len(set(lineages)):
            raise ValidationError("Escolha uma só versão de cada amostra.")
        return samples


class StandardForm(CatalogForm):
    class Meta:
        model = Standard
        fields = ["identifier", "title", "scope"]
        help_texts = {"identifier": "Ex.: NBR ISO 13485:2016."}

    def clean_identifier(self):
        return " ".join((self.cleaned_data.get("identifier") or "").split())


class ReferenceForm(CatalogForm):
    class Meta:
        model = BibliographicReference
        fields = ["citation", "year", "doi_or_url"]
        widgets = {"citation": forms.Textarea(attrs={"rows": 3})}

    def clean_year(self):
        year = self.cleaned_data.get("year")
        if year is not None and not 1500 <= year <= timezone.localdate().year + 1:
            raise ValidationError("Ano fora do intervalo aceito.")
        return year


FORMS = {
    "lotes": LotForm,
    "insumos": MaterialForm,
    "kits": ReferenceKitForm,
    "amostras": SampleForm,
    "paineis": PanelForm,
    "normas": StandardForm,
    "referencias": ReferenceForm,
}


class StatusForm(forms.Form):
    action = forms.ChoiceField(choices=[("desativar", "Desativar"), ("reativar", "Reativar")])
    reason = forms.CharField(label="Motivo", widget=forms.Textarea(attrs={"rows": 2}))


class ImportForm(forms.Form):
    spreadsheet = forms.FileField(
        label="Planilha de insumos",
        help_text="CSV (separador ; ou ,) ou XLSX, no layout da planilha modelo; até 5.000 linhas.",
    )

    def clean_spreadsheet(self):
        uploaded = self.cleaned_data["spreadsheet"]
        check_upload(uploaded, SPREADSHEET_KINDS)
        return uploaded
