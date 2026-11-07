from django import forms
from django.contrib.auth import get_user_model
from django.forms import formset_factory

from sgp.accounts.models import ProfileAssignment
from sgp.accounts.profiles import Profile
from sgp.vocab.models import SUBDOCUMENT_TYPE, TECHNOLOGY, Term, active_terms

from .fields import BRLMoneyField, LinesField
from .models import ProjectStatus, RegulatoryBody, RiskClass

DATE_WIDGET = {"type": "date"}


def _date_field(label, required=False):
    return forms.DateField(
        label=label, required=required, widget=forms.DateInput(attrs=DATE_WIDGET, format="%Y-%m-%d")
    )


def leaders_queryset():
    leader_ids = ProfileAssignment.objects.filter(
        profile=Profile.PROJECT_LEADER, revoked_at__isnull=True
    ).values("user_id")
    return get_user_model().objects.filter(pk__in=leader_ids, is_active=True).order_by("full_name")


class ProductForm(forms.Form):
    title = forms.CharField(label="Nome do projeto", max_length=200)
    product_name = forms.CharField(label="Nome do produto", max_length=200)
    product_family = forms.CharField(
        label="Família (quando houver)", max_length=200, required=False
    )
    technology = forms.ModelChoiceField(label="Tecnologia", queryset=None)
    regulatory_body = forms.ChoiceField(label="Órgão regulador", choices=RegulatoryBody.choices)
    risk_class = forms.ChoiceField(
        label="Classe de risco prevista (RDC 830/2023)",
        choices=[("", "—"), *RiskClass.choices],
        required=False,
        help_text="Obrigatória para submeter projetos ANVISA; não se aplica a projetos MAPA.",
    )
    classification_rule = forms.CharField(
        label="Regra de classificação",
        max_length=200,
        required=False,
        help_text='Ex.: "Regra 5, item d".',
    )
    row_version = forms.IntegerField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, with_leader=False, **kwargs):
        super().__init__(*args, **kwargs)
        current = self.initial.get("technology")
        queryset = active_terms(TECHNOLOGY)
        if current:
            # Termo desativado depois continua válido no projeto que já o usa (FR-019 da 003).
            queryset = queryset | Term.objects.of(TECHNOLOGY).filter(pk=current)
        self.fields["technology"].queryset = queryset
        if with_leader:
            self.fields["leader"] = forms.ModelChoiceField(
                label="Líder do projeto", queryset=leaders_queryset()
            )

    def product_data(self) -> dict:
        data = self.cleaned_data
        return {
            field: data[field]
            for field in (
                "title",
                "product_name",
                "product_family",
                "technology",
                "regulatory_body",
                "risk_class",
                "classification_rule",
            )
        }


class RiskForm(forms.Form):
    risco = forms.CharField(label="Risco", max_length=500, required=False)
    impacto = forms.CharField(label="Impacto", max_length=500, required=False)
    resposta = forms.CharField(label="Resposta", max_length=500, required=False)


class StakeholderForm(forms.Form):
    nome_area = forms.CharField(label="Nome/área", max_length=300, required=False)
    interesse = forms.CharField(label="Interesse", max_length=500, required=False)


RiskFormSet = formset_factory(RiskForm, extra=3, can_delete=True)
StakeholderFormSet = formset_factory(StakeholderForm, extra=3, can_delete=True)


def rows_from_formset(formset, keys) -> list[dict]:
    rows = []
    for form in formset:
        if not form.cleaned_data or form.cleaned_data.get("DELETE"):
            continue
        row = {key: (form.cleaned_data.get(key) or "").strip() for key in keys}
        if any(row.values()):
            rows.append(row)
    return rows


class CharterForm(forms.Form):
    justification = forms.CharField(
        label="Justificativa", widget=forms.Textarea(attrs={"rows": 4}), required=False
    )
    objective = forms.CharField(
        label="Objetivo", widget=forms.Textarea(attrs={"rows": 3}), required=False
    )
    scope_included = LinesField(label="Escopo incluído")
    scope_excluded = LinesField(label="Escopo excluído")
    deliverables = LinesField(label="Entregas")
    assumptions = LinesField(label="Premissas")
    constraints = LinesField(label="Restrições")
    row_version = forms.IntegerField(widget=forms.HiddenInput, required=False)


class BusinessPlanForm(forms.Form):
    plan_date = _date_field("Data do plano")
    objective = forms.CharField(
        label="Objetivo", widget=forms.Textarea(attrs={"rows": 3}), required=False
    )
    description = forms.CharField(
        label="Descrição geral", widget=forms.Textarea(attrs={"rows": 4}), required=False
    )
    total_cost = BRLMoneyField(label="Custo total do projeto (R$)", required=False)
    execution_months = forms.IntegerField(
        label="Prazo de execução (meses)", min_value=1, required=False
    )
    execution_end_date = _date_field("Término previsto")
    target_market = forms.CharField(
        label="Mercado-alvo", widget=forms.Textarea(attrs={"rows": 3}), required=False
    )
    competitors = LinesField(label="Principais concorrentes")
    competitor_price_min = BRLMoneyField(
        label="Preço por teste dos concorrentes — mínimo (R$)", required=False
    )
    competitor_price_max = BRLMoneyField(
        label="Preço por teste dos concorrentes — máximo (R$)", required=False
    )
    competitor_presentations = LinesField(
        label="Principais apresentações dos kits dos concorrentes"
    )
    max_production_cost = BRLMoneyField(
        label="Custo máximo de produção, considerando matéria-prima (R$)", required=False
    )
    sale_price_min = BRLMoneyField(label="Previsão de preço de venda — mínimo (R$)", required=False)
    sale_price_max = BRLMoneyField(label="Previsão de preço de venda — máximo (R$)", required=False)
    annual_sales_tests = forms.IntegerField(
        label="Previsão de venda anual (testes/ano)", min_value=0, required=False
    )
    factory_structure = forms.CharField(
        label="Avaliação da estrutura fabril para produção do kit",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
    )
    production_team = forms.CharField(
        label="Avaliação da equipe de Produção",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
    )
    quality_control = forms.CharField(
        label="Avaliação do Controle de Qualidade",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
    )
    forecast_1 = BRLMoneyField(label="Retorno esperado — ano 1 (R$)", required=False)
    forecast_2 = BRLMoneyField(label="Retorno esperado — ano 2 (R$)", required=False)
    forecast_3 = BRLMoneyField(label="Retorno esperado — ano 3 (R$)", required=False)
    forecast_4 = BRLMoneyField(label="Retorno esperado — ano 4 (R$)", required=False)
    forecast_5 = BRLMoneyField(label="Retorno esperado — ano 5 (R$)", required=False)
    row_version = forms.IntegerField(widget=forms.HiddenInput, required=False)

    PLAN_KEYS = (
        "plan_date",
        "objective",
        "description",
        "total_cost",
        "execution_months",
        "execution_end_date",
        "target_market",
        "competitors",
        "competitor_price_min",
        "competitor_price_max",
        "competitor_presentations",
        "max_production_cost",
        "sale_price_min",
        "sale_price_max",
        "annual_sales_tests",
        "factory_structure",
        "production_team",
        "quality_control",
    )

    def clean(self):
        cleaned = super().clean()
        for low, high, label in (
            ("competitor_price_min", "competitor_price_max", "preço dos concorrentes"),
            ("sale_price_min", "sale_price_max", "preço de venda previsto"),
        ):
            if (
                cleaned.get(low) is not None
                and cleaned.get(high) is not None
                and cleaned[low] > cleaned[high]
            ):
                self.add_error(
                    high, f"Na faixa de {label}, o máximo não pode ser menor que o mínimo."
                )
        return cleaned

    def plan_data(self) -> dict:
        return {key: self.cleaned_data.get(key) for key in self.PLAN_KEYS}

    def forecasts(self) -> dict[int, object]:
        return {year: self.cleaned_data.get(f"forecast_{year}") for year in range(1, 6)}


class MemberForm(forms.Form):
    user = forms.ModelChoiceField(label="Pessoa", queryset=None)
    role = forms.CharField(label="Papel no projeto", max_length=200)
    start_date = _date_field("Início da vigência")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = (
            get_user_model().objects.filter(is_active=True).order_by("full_name")
        )


class EndMemberForm(forms.Form):
    end_date = _date_field("Fim da vigência")
    reason = forms.CharField(
        label="Motivo", max_length=2000, widget=forms.Textarea(attrs={"rows": 2})
    )


class MilestoneForm(forms.Form):
    subdocument_type = forms.ModelChoiceField(label="Subdocumento", queryset=None)
    description = forms.CharField(label="Descrição", max_length=200, required=False)
    planned_date = _date_field("Data planejada", required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subdocument_type"].queryset = active_terms(SUBDOCUMENT_TYPE)


class MilestoneUpdateForm(forms.Form):
    planned_date = _date_field("Data planejada")
    actual_date = _date_field("Data realizada")


class ReasonForm(forms.Form):
    reason = forms.CharField(
        label="Motivo", max_length=2000, widget=forms.Textarea(attrs={"rows": 2})
    )


class ReturnForm(forms.Form):
    comment = forms.CharField(
        label="Comentário da devolução", max_length=4000, widget=forms.Textarea(attrs={"rows": 3})
    )


class ProjectFilterForm(forms.Form):
    status = forms.ChoiceField(
        label="Situação", choices=[("", "Todas"), *ProjectStatus.choices], required=False
    )
    lider = forms.ModelChoiceField(
        label="Líder", queryset=None, required=False, empty_label="Todos"
    )
    produto = forms.CharField(label="Produto", max_length=200, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Project

        leader_ids = Project.objects.values("leader_id")
        self.fields["lider"].queryset = (
            get_user_model().objects.filter(pk__in=leader_ids).order_by("full_name")
        )
