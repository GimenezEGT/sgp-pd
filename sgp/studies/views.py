"""Telas dos estudos (contrato rotas-ui.md da feature 007)."""

import re
from decimal import Decimal

from django import forms
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from sgp.accounts.profiles import deny_access
from sgp.core.formatting import format_decimal_br
from sgp.formtemplates.fieldtypes import parse_number
from sgp.projects.models import Project
from sgp.subdocuments.models import Subdocument
from sgp.vocab.models import Term

from . import importing, profiles, services
from .models import CIMethod, CutoffDirection, ImportMapping, Rounding, Study

BLANK_ROWS = 5
ROW_FIELD = re.compile(r"^r__(\d+)__([a-z]+)$")
CRITERION_FIELD = re.compile(r"^c__(\d+)__([a-z]+)$")


class StudyForm(forms.Form):
    study_type = forms.ModelChoiceField(label="Tipo de estudo", queryset=Term.objects.none())
    title = forms.CharField(label="Título", max_length=200)
    link = forms.ChoiceField(label="Alimenta o tópico", required=False)
    rounding = forms.ChoiceField(label="Arredondamento", choices=Rounding.choices)
    ci_method = forms.ChoiceField(label="IC 95% de proporções", choices=CIMethod.choices)
    cutoff = forms.CharField(label="Valor de corte (só cut-off)", required=False)
    cutoff_direction = forms.ChoiceField(
        label="Interpretação do corte", choices=CutoffDirection.choices
    )

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["study_type"].queryset = Term.objects.of(services.STUDY_VOCABULARY).filter(
            is_active=True
        )
        choices = [("", "— sem vínculo —")]
        for sub in Subdocument.objects.filter(
            project=project, subdocument_type__code__in=services.LINKABLE_TYPES
        ).select_related("subdocument_type", "template"):
            for topic in sub.template.topics:
                choices.append((f"{sub.pk}:{topic['key']}", f"{sub} › {topic['label']}"))
        self.fields["link"].choices = choices

    def clean_cutoff(self):
        try:
            return parse_number(self.cleaned_data.get("cutoff", ""))
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc

    def data_for_service(self) -> dict:
        data = dict(self.cleaned_data)
        link = data.pop("link", "")
        data["subdocument"], data["topic_key"] = None, ""
        if link:
            sub_pk, _, key = link.partition(":")
            data["subdocument"] = Subdocument.objects.select_related(
                "subdocument_type", "template"
            ).get(pk=sub_pk)
            data["topic_key"] = key
        return data


def _deny_project(request, project):
    if not services.can_view(request.user, project):
        return deny_access(request, "sem acesso ao projeto")
    return None


def _latest(project):
    latest = {}
    for study in (
        Study.objects.filter(project=project)
        .select_related("study_type", "subdocument")
        .order_by("lineage", "-version")
    ):
        latest.setdefault(study.lineage, study)
    return sorted(latest.values(), key=lambda s: s.title)


@require_http_methods(["GET", "POST"])
def project_studies(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    denied = _deny_project(request, project)
    if denied:
        return denied
    form = StudyForm(request.POST or None, project=project)
    if request.method == "POST":
        if not services.can_edit(request.user, project):
            return deny_access(request, "só os editores do projeto criam estudos")
        if form.is_valid():
            try:
                study = services.create_study(
                    project, by=request.user, data=form.data_for_service()
                )
            except ValidationError as exc:
                for message in exc.messages:
                    messages.error(request, message)
            else:
                messages.success(
                    request, "Estudo criado; defina o critério antes de lançar resultados."
                )
                return redirect("studies:detail", pk=study.pk)
    context = {
        "project": project,
        "studies": _latest(project),
        "form": form,
        "can_edit": services.can_edit(request.user, project),
    }
    return render(request, "studies/list.html", context)


def _display(item: dict) -> str:
    if item.get("arredondado") is None:
        return "não calculável"
    text = item["arredondado"]
    places = len(text.partition(".")[2])
    return format_decimal_br(Decimal(text), places)


def _result_rows(items):
    out = []
    for item in items:
        ic = item.get("ic")
        out.append(
            {
                "rotulo": item["rotulo"],
                "valor": _display(item),
                "ic": " a ".join(
                    format_decimal_br(Decimal(v), len(v.partition(".")[2])) for v in ic
                )
                if ic
                else "",
                "regra": item.get("regra", ""),
            }
        )
    return out


def _row_cells(study, profile):
    rows = []
    for row in study.rows:
        cells = []
        for column in profile.columns:
            value = row.get(column, "")
            if isinstance(value, dict):
                value = value.get("codigo", "")
            elif column in ("x", "y") and value != "":
                value = str(value).replace(".", ",")
            cells.append({"column": column, "value": value})
        rows.append(cells)
    return rows


@require_GET
def study_detail(request, pk):
    study = get_object_or_404(
        Study.objects.select_related("study_type", "project", "subdocument"), pk=pk
    )
    denied = _deny_project(request, study.project)
    if denied:
        return denied
    profile = services.profile_of(study.study_type)
    results = study.results or {}
    context = {
        "study": study,
        "profile": profile,
        "columns": [(c, profiles.COLUMN_LABELS[c]) for c in profile.columns],
        "rows": _row_cells(study, profile),
        "blank_rows": range(len(study.rows), len(study.rows) + BLANK_ROWS),
        "global_results": _result_rows(results.get("global", [])),
        "group_results": [
            {"rotulo": g["rotulo"], "itens": _result_rows(g["metricas"])}
            for g in results.get("grupos", [])
        ],
        "criteria_results": [
            {
                **c,
                "limite": str(c["limite"]).replace(".", ","),
                "valor": (c["valor"] or "").replace(".", ","),
            }
            for c in results.get("criterios", [])
        ],
        "metrics": [(m, profiles.LABELS[m]) for m in profile.criteria],
        "comparisons": list(profiles.COMPARISONS.items()),
        "can_edit": services.can_edit(request.user, study.project) and not study.is_locked,
        "can_new_version": services.can_edit(request.user, study.project) and study.is_locked,
        "versions": Study.objects.filter(lineage=study.lineage).order_by("-version"),
    }
    return render(request, "studies/detail.html", context)


def _indexed(post, pattern):
    grouped = {}
    for key, value in post.items():
        match = pattern.match(key)
        if match:
            grouped.setdefault(int(match.group(1)), {})[match.group(2)] = value
    return [grouped[index] for index in sorted(grouped)]


@require_POST
def study_edit(request, pk):
    study = get_object_or_404(Study.objects.select_related("study_type", "project"), pk=pk)
    denied = _deny_project(request, study.project)
    if denied:
        return denied
    try:
        if request.POST.get("acao") == "criterios":
            criteria = [c for c in _indexed(request.POST, CRITERION_FIELD) if c.get("metrica")]
            services.set_criteria(study, by=request.user, criteria=criteria)
            messages.success(request, "Critério de aceitação gravado.")
        else:
            rows = [
                r
                for r in _indexed(request.POST, ROW_FIELD)
                if any(str(v).strip() for v in r.values())
            ]
            services.save_rows(
                study, by=request.user, raw_rows=rows, row_version=request.POST.get("row_version")
            )
            messages.success(request, "Medidas gravadas e resultados recalculados.")
    except PermissionDenied:
        return deny_access(request, "só os editores do projeto alteram estudos")
    except ValidationError as exc:
        for message in exc.messages:
            messages.error(request, message)
    return redirect("studies:detail", pk=pk)


@require_POST
def study_not_applicable(request, pk):
    study = get_object_or_404(Study.objects.select_related("study_type", "project"), pk=pk)
    denied = _deny_project(request, study.project)
    if denied:
        return denied
    try:
        services.mark_not_applicable(
            study,
            by=request.user,
            justification=request.POST.get("justificativa", ""),
            value=request.POST.get("desmarcar") != "1",
        )
    except PermissionDenied:
        return deny_access(request, "só os editores do projeto alteram estudos")
    except ValidationError as exc:
        for message in exc.messages:
            messages.error(request, message)
    return redirect("studies:detail", pk=pk)


@require_POST
def study_new_version(request, pk):
    study = get_object_or_404(Study.objects.select_related("study_type", "project"), pk=pk)
    denied = _deny_project(request, study.project)
    if denied:
        return denied
    try:
        new = services.new_version(study, by=request.user, reason=request.POST.get("motivo", ""))
    except PermissionDenied:
        return deny_access(request, "só os editores do projeto alteram estudos")
    except ValidationError as exc:
        for message in exc.messages:
            messages.error(request, message)
        return redirect("studies:detail", pk=pk)
    messages.success(
        request, f"Versão {new.version_display} criada; a anterior continua no documento aprovado."
    )
    return redirect("studies:detail", pk=new.pk)


@require_http_methods(["GET", "POST"])
def study_import(request, pk):
    study = get_object_or_404(Study.objects.select_related("study_type", "project"), pk=pk)
    denied = _deny_project(request, study.project)
    if denied:
        return denied
    if not services.can_edit(request.user, study.project):
        return deny_access(request, "só os editores do projeto importam medidas")
    profile = services.profile_of(study.study_type)
    equipment = (
        request.POST.get("equipamento", "").strip() or request.GET.get("equipamento", "").strip()
    )
    saved = ImportMapping.objects.filter(equipment=equipment).first() if equipment else None
    mapping = {
        column: request.POST.get(
            f"col__{column}", (saved.mapping.get(column, "") if saved else "")
        ).strip()
        for column in profile.columns
    }
    context = {
        "study": study,
        "columns": [(c, profiles.COLUMN_LABELS[c], mapping.get(c, "")) for c in profile.columns],
        "equipment": equipment,
        "mappings": ImportMapping.objects.all(),
        "preview": None,
    }
    if request.method == "POST":
        try:
            if request.POST.get("acao") == "confirmar":
                count = importing.confirm(
                    study,
                    by=request.user,
                    token=request.POST.get("token", ""),
                    equipment=equipment,
                    mapping=mapping,
                )
                messages.success(
                    request, f"{count} linha(s) importada(s); resultados recalculados."
                )
                return redirect("studies:detail", pk=pk)
            uploaded = request.FILES.get("arquivo")
            if uploaded is None:
                raise ValidationError("Escolha o arquivo CSV ou XLSX.")
            context["preview"] = importing.preview(
                study, uploaded, {k: v for k, v in mapping.items() if v}
            )
        except ValidationError as exc:
            for message in exc.messages:
                messages.error(request, message)
    return render(request, "studies/import.html", context)
