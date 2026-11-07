"""Telas genéricas dos cadastros, busca enquanto digita e importação de insumos (feature 003)."""

from functools import reduce
from operator import or_

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from sgp.accounts.profiles import deny_access, profile_required
from sgp.audit.models import AuditEvent
from sgp.audit.presentation import EventPresenter
from sgp.files.storage import DOCUMENT_KINDS, store_upload

from . import importing, versioning
from .forms import FORMS, ImportForm, StatusForm
from .kinds import KINDS, MATERIALS, Kind, display_rows, get_kind, value_of
from .models import ImportBatch, ImportStatus
from .permissions import (
    EDITOR_PROFILES,
    can_edit_catalog,
    can_edit_record,
    can_view_record,
    visible_lot_projects,
)

SEARCH_LIMIT = 20
PAGE_SIZE = 50
OUTCOME_MESSAGES = {
    versioning.UNCHANGED: "Nada mudou; nenhuma versão foi criada.",
    versioning.UPDATED: "Cadastro corrigido.",
}


def _errors(request, exc: ValidationError) -> None:
    for message in exc.messages:
        messages.error(request, message)


def _visible(kind: Kind, user, queryset):
    if kind.project_scoped:
        queryset = queryset.filter(project__in=visible_lot_projects(user)).select_related("project")
    return queryset


def _search(kind: Kind, queryset, term: str):
    term = (term or "").strip()
    if not term:
        return queryset
    return queryset.filter(
        reduce(or_, (Q(**{f"{name}__icontains": term}) for name in kind.search_fields))
    )


def _rows(kind: Kind, records) -> list[dict]:
    return [
        {
            "record": record,
            "cells": [value_of(record, accessor) for _, accessor in kind.columns],
        }
        for record in records
    ]


def _get_record(request, kind: Kind, pk):
    record = get_object_or_404(kind.model, pk=pk)
    if not can_view_record(request.user, record):
        return None, deny_access(request, "sem acesso ao projeto do lote")
    return record, None


# ------------------------------------------------------------------- consulta


@require_GET
def index(request):
    return render(
        request,
        "catalog/index.html",
        {"kinds": KINDS.values(), "can_edit": can_edit_catalog(request.user)},
    )


@require_GET
def record_list(request, kind):
    kind = get_kind(kind)
    queryset = _visible(kind, request.user, kind.model.objects.current())
    project_id = request.GET.get("projeto", "")
    if kind.project_scoped and project_id.isdigit():
        queryset = queryset.filter(project_id=int(project_id))
    show_inactive = request.GET.get("inativos") == "1"
    if not show_inactive:
        queryset = queryset.filter(is_active=True)
    term = request.GET.get("q", "")
    queryset = _search(kind, queryset, term).order_by(*kind.search_fields[:1], "pk")
    page = Paginator(queryset, PAGE_SIZE).get_page(request.GET.get("pagina"))
    context = {
        "kind": kind,
        "page": page,
        "rows": _rows(kind, page.object_list),
        "q": term,
        "show_inactive": show_inactive,
        "projects": visible_lot_projects(request.user) if kind.project_scoped else None,
        "project_id": project_id,
        "can_edit": can_edit_catalog(request.user),
        "is_materials": kind is MATERIALS,
    }
    return render(request, "catalog/list.html", context)


@require_GET
def search(request, kind):
    """Fragmento HTML com até 20 cadastros vigentes e ativos (FR-007); usado com HTMX."""
    kind = get_kind(kind)
    term = request.GET.get("q", "").strip()
    results = []
    if term:
        queryset = _visible(kind, request.user, kind.model.objects.available())
        project_id = request.GET.get("projeto", "")
        if kind.project_scoped and project_id.isdigit():
            queryset = queryset.filter(project_id=int(project_id))
        results = list(
            _search(kind, queryset, term).order_by(*kind.search_fields[:1])[:SEARCH_LIMIT]
        )
    return render(
        request,
        "catalog/_search_results.html",
        {"kind": kind, "results": results, "q": term, "is_materials": kind is MATERIALS},
    )


@require_GET
def record_detail(request, kind, pk):
    kind = get_kind(kind)
    record, denied = _get_record(request, kind, pk)
    if denied:
        return denied
    versions = list(versioning.history(record))
    current = next((version for version in versions if version.is_current), None)
    events = EventPresenter(request.user).decorate(
        AuditEvent.objects.filter(
            object_type=kind.object_type, object_id=str(record.lineage)
        ).order_by("seq")
    )
    context = {
        "kind": kind,
        "record": record,
        "current": current,
        "rows": display_rows(record),
        "versions": versions,
        "events": events,
        "samples": record.active_links() if kind.has_samples else None,
        "can_edit": can_edit_record(request.user, record) and record.is_current,
        "status_form": StatusForm(),
        "is_materials": kind is MATERIALS,
    }
    return render(request, "catalog/detail.html", context)


# ------------------------------------------------------------------- edição


def _form(kind: Kind, request, **kwargs):
    form_class = FORMS[kind.slug]
    return form_class(request.POST or None, request.FILES or None, user=request.user, **kwargs)


def _with_certificate(kind: Kind, form, data: dict, by) -> dict:
    uploaded = form.cleaned_data.get("certificate_file") if kind is MATERIALS else None
    if uploaded:
        data = {**data, "certificate": store_upload(uploaded, by=by, allowed=DOCUMENT_KINDS)}
    return data


@require_http_methods(["GET", "POST"])
@profile_required(*EDITOR_PROFILES)
def record_new(request, kind):
    kind = get_kind(kind)
    form = _form(kind, request)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                data = _with_certificate(kind, form, form.model_data(), request.user)
                record = versioning.create_record(
                    kind,
                    by=request.user,
                    data=data,
                    samples=form.cleaned_data.get("samples") if kind.has_samples else None,
                )
        except ValidationError as exc:
            _errors(request, exc)
        else:
            messages.success(request, "Cadastro criado na versão 01.")
            return redirect("catalog:detail", kind=kind.slug, pk=record.pk)
    return render(request, "catalog/form.html", {"kind": kind, "form": form, "record": None})


@require_http_methods(["GET", "POST"])
@profile_required(*EDITOR_PROFILES)
def record_edit(request, kind, pk):
    kind = get_kind(kind)
    record, denied = _get_record(request, kind, pk)
    if denied:
        return denied
    if not record.is_current:
        current = versioning.current_of(record)
        messages.warning(request, versioning.NOT_CURRENT)
        return redirect("catalog:edit", kind=kind.slug, pk=current.pk)
    form = _form(kind, request, instance=record)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                data = _with_certificate(kind, form, form.model_data(), request.user)
                result, outcome = versioning.update_record(
                    record,
                    by=request.user,
                    data=data,
                    reason=form.cleaned_data.get("reason", ""),
                    row_version=form.cleaned_data.get("row_version"),
                    samples=form.cleaned_data.get("samples") if kind.has_samples else None,
                )
        except ValidationError as exc:
            _errors(request, exc)
        else:
            if outcome == versioning.VERSIONED:
                messages.success(
                    request,
                    f"Nova versão {result.version_display} criada; a versão anterior continua "
                    "como estava.",
                )
            else:
                messages.success(request, OUTCOME_MESSAGES[outcome])
            return redirect("catalog:detail", kind=kind.slug, pk=result.pk)
    return render(request, "catalog/form.html", {"kind": kind, "form": form, "record": record})


@require_POST
@profile_required(*EDITOR_PROFILES)
def record_status(request, kind, pk):
    kind = get_kind(kind)
    record, denied = _get_record(request, kind, pk)
    if denied:
        return denied
    form = StatusForm(request.POST)
    if form.is_valid():
        active = form.cleaned_data["action"] == "reativar"
        try:
            versioning.set_active(
                record, by=request.user, active=active, reason=form.cleaned_data["reason"]
            )
        except ValidationError as exc:
            _errors(request, exc)
        else:
            messages.success(request, "Cadastro reativado." if active else "Cadastro desativado.")
    else:
        messages.error(request, versioning.STATUS_REASON)
    return redirect("catalog:detail", kind=kind.slug, pk=record.pk)


# --------------------------------------------------------------- importação


@require_http_methods(["GET", "POST"])
@profile_required(*EDITOR_PROFILES)
def import_upload(request):
    form = ImportForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        try:
            batch = importing.preview(form.cleaned_data["spreadsheet"], by=request.user)
        except ValidationError as exc:
            form.add_error("spreadsheet", exc)
        else:
            return redirect("catalog:import_batch", pk=batch.pk)
    recent = ImportBatch.objects.select_related("source_file", "uploaded_by")[:10]
    return render(request, "catalog/import_upload.html", {"form": form, "recent": recent})


@require_http_methods(["GET", "POST"])
@profile_required(*EDITOR_PROFILES)
def import_batch(request, pk):
    batch = get_object_or_404(ImportBatch.objects.select_related("source_file"), pk=pk)
    if request.method == "POST":
        try:
            batch = importing.confirm(batch, by=request.user)
        except ValidationError as exc:
            _errors(request, exc)
        else:
            messages.success(
                request,
                f"Importação confirmada: {batch.created_count} insumo(s) criado(s) e "
                f"{batch.rejected_count} linha(s) rejeitada(s).",
            )
        return redirect("catalog:import_batch", pk=batch.pk)
    rejected = batch.rejected_rows()
    context = {
        "batch": batch,
        "rejected": rejected[:500],
        "valid_preview": [row for row in batch.rows if not row["erros"]][:50],
        "is_preview": batch.status == ImportStatus.PREVIEW,
    }
    return render(request, "catalog/import_batch.html", context)


@require_GET
@profile_required(*EDITOR_PROFILES)
def import_rejections(request, pk):
    batch = get_object_or_404(ImportBatch, pk=pk)
    response = HttpResponse(
        importing.rejection_report(batch), content_type="text/csv; charset=utf-8"
    )
    response["Content-Disposition"] = f'attachment; filename="rejeicoes-importacao-{batch.pk}.csv"'
    return response


@require_GET
@profile_required(*EDITOR_PROFILES)
def import_template(request):
    response = HttpResponse(importing.template_csv(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="modelo-importacao-insumos.csv"'
    return response
