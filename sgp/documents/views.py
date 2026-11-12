"""Telas da geração de documentos e dos modelos de layout (contrato rotas-ui.md da feature 006)."""

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import content_disposition_header
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from sgp.accounts.profiles import Profile, active_profiles, deny_access, profile_required
from sgp.files.storage import IntegrityFailure, read_verified
from sgp.signatures.documents import load
from sgp.vocab.models import Term

from . import layouts, preview, render_pdf, services
from .forms import FIELDS, LayoutForm
from .layouts import LogoIntegrityError
from .models import (
    GeneratedDocument,
    GenerationRequest,
    LayoutStatus,
    LayoutTarget,
    LayoutTemplate,
    OutputFormat,
)

NO_ACCESS_REASON = "sem acesso ao documento"


def _is_htmx(request) -> bool:
    return request.headers.get("HX-Request") == "true"


def _document_or_deny(request, kind, pk):
    adapter, obj = load(kind, pk)
    if not services.can_view_document(request.user, kind, obj):
        return adapter, obj, deny_access(request, NO_ACCESS_REASON)
    return adapter, obj, None


# ------------------------------------------------------------------ documentos


@require_GET
def document_history(request, kind, pk):
    adapter, obj, denied = _document_or_deny(request, kind, pk)
    if denied:
        return denied
    context = {
        "kind": kind,
        "obj": obj,
        "title": adapter.title(obj),
        "version": f"{adapter.version(obj):02d}",
        "status": adapter.status(obj),
        "approved": adapter.status(obj) == "approved",
        "back_url": adapter.url(obj),
        "requests": services.active_requests(kind, obj),
        "history": services.history(kind, obj),
        "formats": OutputFormat.choices,
    }
    return render(request, "documents/history.html", context)


@require_POST
def generate(request, kind, pk):
    adapter, obj, denied = _document_or_deny(request, kind, pk)
    if denied:
        return denied
    try:
        pending = services.request_generation(
            kind, obj, request.POST.get("formato", ""), by=request.user, request=request
        )
    except PermissionDenied:
        return deny_access(request, NO_ACCESS_REASON)
    except ValidationError as exc:
        for message in exc.messages:
            messages.error(request, message)
        return redirect("documents:history", kind=kind, pk=pk)
    if _is_htmx(request):
        return render(request, "documents/_request.html", {"pending": pending})
    messages.success(request, "Pedido registrado; a situação aparece abaixo.")
    return redirect("documents:history", kind=kind, pk=pk)


@require_GET
def request_status(request, pk):
    pending = get_object_or_404(GenerationRequest, pk=pk)
    _adapter, _obj, denied = _document_or_deny(request, pending.kind, pending.object_id)
    if denied:
        return denied
    return render(request, "documents/_request.html", {"pending": pending})


@require_GET
def download(request, pk):
    generated = get_object_or_404(GeneratedDocument.objects.select_related("file"), pk=pk)
    _adapter, _obj, denied = _document_or_deny(request, generated.kind, generated.object_id)
    if denied:
        return denied
    try:
        data = read_verified(generated.file)
    except IntegrityFailure as failure:
        # Resposta normal (sem exceção) para o evento não ser desfeito com a transação.
        services.integrity_failed(failure, request=request)
        return render(
            request, "files/integrity_failed.html", {"stored": generated.file}, status=409
        )
    services.record_download(generated, by=request.user, request=request)
    response = HttpResponse(data, content_type=generated.file.content_type)
    response["Content-Disposition"] = content_disposition_header(
        as_attachment=True, filename=generated.file.original_name
    )
    response["X-Content-Type-Options"] = "nosniff"
    return response


@require_GET
def verify(request):
    code = request.GET.get("codigo", "").strip()
    result = services.lookup(code, user=request.user, request=request) if code else None
    return render(request, "documents/verify.html", {"code": code, "result": result})


# ------------------------------------------------------------------ modelos de layout


def _is_quality(user) -> bool:
    return Profile.QUALITY in active_profiles(user)


def _type_terms(layout):
    if layout.target != LayoutTarget.SUBDOCUMENT:
        return []
    return list(Term.objects.of("tipo-subdocumento").filter(is_active=True).order_by("position"))


@require_GET
def layout_list(request):
    rows = []
    for target, label in LayoutTarget.choices:
        versions = list(LayoutTemplate.objects.filter(target=target).order_by("-version"))
        rows.append(
            {
                "target": target,
                "label": label,
                "current": layouts.current_layout(target),
                "draft": next((v for v in versions if v.status == LayoutStatus.DRAFT), None),
                "versions": versions,
            }
        )
    return render(
        request,
        "documents/layouts/list.html",
        {"rows": rows, "is_quality": _is_quality(request.user)},
    )


def _parameters(layout) -> list[tuple[str, str]]:
    definition = layout.definition
    items = [(label, definition[section][key]) for section, key, _n, label, *_ in FIELDS]
    for code, size in definition["cover"].get("title_pt_by_type", {}).items():
        items.append((f"Título de {code} (pt)", size))
    for code, variant in definition["cover"].get("variant_by_type", {}).items():
        items.append((f"Capa de {code}", variant))
    return items


@require_GET
def layout_detail(request, pk):
    layout = get_object_or_404(LayoutTemplate, pk=pk)
    context = {
        "layout": layout,
        "current": layouts.current_layout(layout.target),
        "parameters": _parameters(layout),
        "is_quality": _is_quality(request.user),
        "can_verify": bool({Profile.QUALITY, Profile.RD_MANAGER} & active_profiles(request.user)),
        "can_decide": Profile.RD_MANAGER in active_profiles(request.user),
        "can_retire": False,  # layout não é retirado de uso (feature 013, esclarecimento 2026-11-11)
    }
    return render(request, "documents/layouts/detail.html", context)


@require_POST
@profile_required(Profile.QUALITY)
def layout_new_version(request, pk):
    source = get_object_or_404(LayoutTemplate, pk=pk)
    try:
        draft = layouts.create_draft(source.target, by=request.user, source=source)
    except ValidationError as exc:
        for message in exc.messages:
            messages.error(request, message)
        return redirect("layouts:detail", pk=source.pk)
    messages.success(request, f"Rascunho da versão {draft.version_display} criado.")
    return redirect("layouts:edit", pk=draft.pk)


@require_http_methods(["GET", "POST"])
@profile_required(Profile.QUALITY)
def layout_edit(request, pk):
    layout = get_object_or_404(LayoutTemplate, pk=pk)
    if layout.status != LayoutStatus.DRAFT:
        messages.error(request, layouts.NOT_DRAFT)
        return redirect("layouts:detail", pk=layout.pk)
    terms = _type_terms(layout)
    form = LayoutForm(
        request.POST or None,
        request.FILES or None,
        initial=LayoutForm.initial_from(layout),
        type_terms=terms,
    )
    if request.method == "POST" and form.is_valid():
        try:
            layout = layouts.update_draft(
                layout,
                by=request.user,
                definition=form.definition(),
                valid_from=form.cleaned_data["valid_from"],
                logo_upload=form.cleaned_data.get("logo"),
                row_version=form.cleaned_data["row_version"],
            )
        except ValidationError as exc:
            for message in exc.messages:
                messages.error(request, message)
        else:
            problems = layouts.definition_errors(layout, layout.definition)
            if problems:
                messages.warning(
                    request, "Rascunho salvo; corrija os pontos abaixo antes de publicar."
                )
            else:
                messages.success(request, "Rascunho salvo e pronto para publicar.")
            return redirect("layouts:edit", pk=layout.pk)
    problems = layouts.definition_errors(layout, layout.definition)
    return render(
        request,
        "documents/layouts/edit.html",
        {"layout": layout, "form": form, "problems": problems},
    )


@require_GET
@profile_required(Profile.QUALITY)
def layout_preview(request, pk):
    layout = get_object_or_404(LayoutTemplate, pk=pk)
    content = preview.sample_content(layout.target)
    try:
        data = render_pdf.render(
            content,
            layout,
            draft=True,
            created=timezone.localtime().replace(microsecond=0).isoformat(),
            identifier=render_pdf.identifier_for("previa", layout.pk),
        )
    except (IntegrityFailure, LogoIntegrityError):
        messages.error(request, "O logotipo desta versão falhou na conferência de integridade.")
        return redirect("layouts:detail", pk=layout.pk)
    response = HttpResponse(data, content_type="application/pdf")
    response["Content-Disposition"] = content_disposition_header(
        as_attachment=False, filename=f"previa-layout-{layout.target}-v{layout.version_display}.pdf"
    )
    response["X-Content-Type-Options"] = "nosniff"
    return response


@require_GET
def layout_logo(request, pk):
    layout = get_object_or_404(LayoutTemplate, pk=pk)
    try:
        data = layouts.logo_bytes(layout)
    except (IntegrityFailure, LogoIntegrityError):
        return HttpResponse(status=409)
    content_type = "image/png" if data.startswith(render_pdf.PNG_SIGNATURE) else "image/jpeg"
    response = HttpResponse(data, content_type=content_type)
    response["X-Content-Type-Options"] = "nosniff"
    return response
