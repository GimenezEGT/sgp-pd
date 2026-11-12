"""Telas dos modelos de formulário: consulta por todos; rascunho e publicação pela Qualidade."""

import json

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from sgp.accounts.profiles import Profile, active_profiles, profile_required
from sgp.vocab.models import Term

from . import schema, services
from .forms import DraftForm
from .models import FormTemplate, TemplateStatus


def _errors(request, exc: ValidationError) -> None:
    for message in exc.messages:
        messages.error(request, message)


def _preview(template: FormTemplate) -> dict:
    numbered = schema.numbered_topics(template.definition)
    cover = [(number, topic) for number, topic in numbered if number]
    columns = template.cover.get("columns", 1)
    half = (len(cover) + 1) // 2 if columns == 2 else len(cover)
    return {
        "numbered": numbered,
        "cover_columns": [cover[:half], cover[half:]] if columns == 2 else [cover],
    }


def _revision_flags(user, template, current) -> dict:
    """Ações da revisão controlada (feature 013) mostradas no detalhe da versão."""
    profiles = active_profiles(user)
    return {
        "can_verify": bool({Profile.QUALITY, Profile.RD_MANAGER} & profiles),
        "can_decide": Profile.RD_MANAGER in profiles,
        "can_retire": Profile.QUALITY in profiles
        and current is not None
        and current.pk == template.pk,
    }


@require_GET
def template_list(request):
    types = Term.objects.of("tipo-subdocumento").order_by("position")
    rows = []
    for term in types:
        versions = list(
            FormTemplate.objects.filter(subdocument_type=term).order_by("-form_version")
        )
        rows.append(
            {
                "type": term,
                "current": services.current_template(term),
                "draft": next((t for t in versions if t.status == TemplateStatus.DRAFT), None),
                "versions": versions,
            }
        )
    is_quality = Profile.QUALITY in active_profiles(request.user)
    return render(request, "formtemplates/list.html", {"rows": rows, "is_quality": is_quality})


@require_GET
def template_detail(request, pk):
    template = get_object_or_404(FormTemplate.objects.select_related("subdocument_type"), pk=pk)
    current = services.current_template(template.subdocument_type)
    context = {
        "template": template,
        "current": current,
        "is_quality": Profile.QUALITY in active_profiles(request.user),
        **_revision_flags(request.user, template, current),
        **_preview(template),
    }
    return render(request, "formtemplates/detail.html", context)


@require_POST
@profile_required(Profile.QUALITY)
def template_new_version(request, pk):
    source = get_object_or_404(FormTemplate, pk=pk)
    try:
        draft = services.create_draft(source.subdocument_type, by=request.user, source=source)
    except ValidationError as exc:
        _errors(request, exc)
        return redirect("formtemplates:detail", pk=source.pk)
    messages.success(request, f"Rascunho da versão {draft.version_display} criado.")
    return redirect("formtemplates:edit", pk=draft.pk)


@require_http_methods(["GET", "POST"])
@profile_required(Profile.QUALITY)
def template_edit(request, pk):
    template = get_object_or_404(FormTemplate.objects.select_related("subdocument_type"), pk=pk)
    if template.status != TemplateStatus.DRAFT:
        messages.error(request, services.NOT_DRAFT)
        return redirect("formtemplates:detail", pk=template.pk)
    initial = {
        "reference": template.reference,
        "valid_from": template.valid_from,
        "definition": json.dumps(template.definition, ensure_ascii=False, indent=2),
        "row_version": template.row_version,
    }
    form = DraftForm(request.POST or None, initial=initial)
    problems = []
    if request.method == "POST" and form.is_valid():
        try:
            template = services.update_draft(
                template,
                by=request.user,
                data=form.cleaned_data,
                definition=form.cleaned_data["definition"],
                row_version=form.cleaned_data["row_version"],
            )
        except ValidationError as exc:
            _errors(request, exc)
        else:
            problems = services.definition_errors(template, template.definition)
            if problems:
                messages.warning(
                    request, "Rascunho salvo; corrija os pontos abaixo antes de publicar."
                )
            else:
                messages.success(request, "Rascunho salvo e pronto para publicar.")
            return redirect("formtemplates:edit", pk=template.pk)
    if request.method == "GET":
        problems = services.definition_errors(template, template.definition)
    context = {"template": template, "form": form, "problems": problems, **_preview(template)}
    return render(request, "formtemplates/edit.html", context)
