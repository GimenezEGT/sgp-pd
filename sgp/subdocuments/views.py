"""Telas dos subdocumentos do projeto (contrato rotas-ui.md da feature 004)."""

import time

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from sgp.accounts.profiles import Profile, deny_access, profile_required
from sgp.audit.models import AuditEvent
from sgp.audit.presentation import EventPresenter
from sgp.formtemplates.services import current_template
from sgp.projects.permissions import get_project_or_deny
from sgp.vocab.models import Term

from . import flow, parsing, permissions, rendering, services
from .models import CHANGE, Subdocument

NO_ACCESS = "sem acesso ao projeto do subdocumento"


def _errors(request, exc: ValidationError) -> None:
    for message in exc.messages:
        messages.error(request, message)


def _get(request, pk):
    subdocument = get_object_or_404(
        Subdocument.objects.select_related("project", "template", "subdocument_type"), pk=pk
    )
    if not permissions.can_view(request.user, subdocument.project):
        return None, deny_access(request, NO_ACCESS)
    return subdocument, None


def _types():
    return Term.objects.of("tipo-subdocumento").order_by("position")


@require_GET
def project_subdocuments(request, project_id):
    project, denied = get_project_or_deny(request, project_id)
    if denied:
        return denied
    documents = list(
        project.subdocuments.select_related("subdocument_type", "template", "review_requested_by")
    )
    rows = []
    for term in _types():
        existing = [doc for doc in documents if doc.subdocument_type_id == term.pk]
        needed = flow.requirement(project, term.code)
        rows.append(
            {
                "type": term,
                "documents": existing,
                "can_create": term.code == CHANGE or not existing,
                "needed": needed,
                "template": current_template(term),
            }
        )
    context = {
        "project": project,
        "rows": rows,
        "can_edit": permissions.can_edit(request.user, project),
        "is_manager": permissions.is_manager(request.user),
    }
    return render(request, "subdocuments/list.html", context)


@require_POST
def subdocument_new(request, project_id):
    project, denied = get_project_or_deny(request, project_id)
    if denied:
        return denied
    if not permissions.can_edit(request.user, project):
        return deny_access(request, "edição de subdocumentos")
    term = get_object_or_404(
        Term.objects.of("tipo-subdocumento"), code=request.POST.get("tipo", "")
    )
    try:
        subdocument = services.create_subdocument(project, term, by=request.user)
    except services.FlowAuthorizationRequired as exc:
        messages.warning(request, exc.messages[0])
        return redirect("subdocuments:project_list", project_id=project.pk)
    except ValidationError as exc:
        _errors(request, exc)
        return redirect("subdocuments:project_list", project_id=project.pk)
    messages.success(request, f"{subdocument} criado em rascunho.")
    return redirect("subdocuments:edit", pk=subdocument.pk)


@require_POST
@profile_required(Profile.RD_MANAGER)
def flow_authorize(request, project_id):
    project, denied = get_project_or_deny(request, project_id)
    if denied:
        return denied
    term = get_object_or_404(
        Term.objects.of("tipo-subdocumento"), code=request.POST.get("tipo", "")
    )
    try:
        services.authorize_flow(
            project, term, by=request.user, reason=request.POST.get("motivo", "")
        )
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(request, f"Criação de {term.label} fora da ordem autorizada.")
    return redirect("subdocuments:project_list", project_id=project.pk)


def _signature_actions(user, subdocument) -> dict:
    from sgp.signatures.services import block_context

    return block_context(user, "subdocument", subdocument)


def _page_context(request, subdocument, *, editing, data=None):
    return {
        "subdocument": subdocument,
        "project": subdocument.project,
        "topics": rendering.topics_view(subdocument, data=data, editing=editing),
        "can_edit": subdocument.is_draft
        and permissions.can_edit(request.user, subdocument.project),
        "signature_actions": _signature_actions(request.user, subdocument),
        "is_manager": permissions.is_manager(request.user),
        "current_template": current_template(subdocument.subdocument_type),
        "has_derived": any(
            field["type"] == "derived_table"
            for topic in subdocument.template.topics
            for field in topic.get("fields", [])
        ),
    }


@require_GET
def subdocument_detail(request, pk):
    subdocument, denied = _get(request, pk)
    if denied:
        return denied
    context = _page_context(request, subdocument, editing=False)
    context["missing"] = services.completeness(subdocument) if subdocument.is_draft else []
    from sgp.studies.services import linked_studies

    context["studies"] = linked_studies(subdocument)  # feature 007
    context["events"] = EventPresenter(request.user).decorate(
        AuditEvent.objects.filter(
            object_type="subdocuments.subdocument", object_id=str(subdocument.pk)
        ).order_by("seq")
    )
    return render(request, "subdocuments/detail.html", context)


@require_http_methods(["GET", "POST"])
def subdocument_edit(request, pk):
    subdocument, denied = _get(request, pk)
    if denied:
        return denied
    if not permissions.can_edit(request.user, subdocument.project):
        return deny_access(request, "edição de subdocumentos")
    if not subdocument.is_draft:
        messages.error(request, services.NOT_DRAFT)
        return redirect("subdocuments:detail", pk=subdocument.pk)
    data = None
    if request.method == "POST":

        def context_for(previous=None):
            return services.context_for(subdocument, by=request.user, previous=previous)

        data, uploads, errors = parsing.parse_post(
            subdocument, request.POST, request.FILES, context_for=context_for
        )
        if errors:
            for message in errors:
                messages.error(request, message)
        else:
            try:
                services.save_subdocument(
                    subdocument,
                    by=request.user,
                    data=data,
                    uploads=uploads,
                    row_version=request.POST.get("row_version"),
                )
            except ValidationError as exc:
                _errors(request, exc)
            else:
                messages.success(request, "Subdocumento salvo.")
                return redirect("subdocuments:edit", pk=subdocument.pk)
    context = _page_context(request, subdocument, editing=True, data=data)
    return render(request, "subdocuments/edit.html", context)


@require_GET
def table_row(request, pk):
    """Fragmento HTMX com uma linha nova (índice único) da tabela pedida."""
    subdocument, denied = _get(request, pk)
    if denied:
        return denied
    if not permissions.can_edit(request.user, subdocument.project):
        return deny_access(request, "edição de subdocumentos")
    topic = subdocument.template.topic(request.GET.get("topico", ""))
    field_def = next(
        (
            f
            for f in (topic or {}).get("fields", [])
            if f["key"] == request.GET.get("campo") and f["type"] == "table"
        ),
        None,
    )
    if field_def is None:
        raise Http404("Tabela inexistente.")
    name = parsing.field_prefix(topic["key"], field_def["key"])
    cells = rendering.blank_row(field_def, name, 1000000 + int(time.time() * 1000) % 1000000000)
    return render(request, "subdocuments/_table_row.html", {"cells": cells})


@require_POST
def refresh(request, pk):
    subdocument, denied = _get(request, pk)
    if denied:
        return denied
    try:
        services.refresh_derived(subdocument, by=request.user)
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(request, "Linhas derivadas atualizadas a partir da Entrada aprovada.")
    return redirect("subdocuments:edit", pk=subdocument.pk)


@require_POST
@profile_required(Profile.RD_MANAGER)
def migrate(request, pk):
    subdocument, denied = _get(request, pk)
    if denied:
        return denied
    try:
        services.migrate_template(
            subdocument, by=request.user, reason=request.POST.get("motivo", "")
        )
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(request, "Documento migrado para a versão vigente do modelo.")
    return redirect("subdocuments:detail", pk=subdocument.pk)
