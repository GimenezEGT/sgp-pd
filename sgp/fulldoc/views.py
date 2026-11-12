"""Telas do documento completo do projeto (contrato rotas-ui.md da feature 009)."""

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import content_disposition_header
from django.views.decorators.http import require_GET, require_http_methods

from sgp.accounts.profiles import deny_access
from sgp.core.access import can_access_project
from sgp.files.storage import IntegrityFailure, record_integrity_failure
from sgp.projects.models import Project
from sgp.projects.permissions import can_view_financials

from . import pending, services
from .models import NOTEBOOK_FULL, NOTEBOOK_SUMMARY, FullDocument, FullDocumentRequest


@require_http_methods(["GET", "POST"])
def project_document(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if not can_access_project(request.user, project):
        return deny_access(request, "sem acesso ao projeto")
    can_generate = services.can_generate(request.user, project)
    if request.method == "POST":
        if not can_generate:
            return deny_access(
                request, "só o líder do projeto e o Gestor de P&D geram o documento completo"
            )
        try:
            services.request_document(
                project,
                by=request.user,
                options={
                    "caderno": request.POST.get("caderno"),
                    "historico_versoes": request.POST.get("historico_versoes") == "1",
                    "omitir_financeiro": request.POST.get("omitir_financeiro") == "1",
                },
                request=request,
            )
        except ValidationError as exc:
            for message in exc.messages:
                messages.error(request, message)
        except PermissionDenied as exc:
            return deny_access(request, str(exc))
        else:
            messages.success(request, "Pedido recebido; o progresso aparece abaixo.")
        return redirect("fulldoc:project", project_id=project.pk)
    documents = [
        {"doc": doc, "can_download": services.can_download(request.user, doc)}
        for doc in services.history(project)
    ]
    latest = FullDocumentRequest.objects.filter(project=project).order_by("-requested_at").first()
    context = {
        "project": project,
        "pending": pending.pending_items(project),
        "can_generate": can_generate,
        "financial": can_view_financials(request.user, project),
        "request_obj": latest,
        "documents": documents,
        "summary": NOTEBOOK_SUMMARY,
        "full": NOTEBOOK_FULL,
    }
    return render(request, "fulldoc/project.html", context)


@require_GET
def request_status(request, pk):
    pending_request = get_object_or_404(
        FullDocumentRequest.objects.select_related("project"), pk=pk
    )
    if not can_access_project(request.user, pending_request.project):
        return deny_access(request, "sem acesso ao projeto")
    return render(request, "fulldoc/_request.html", {"request_obj": pending_request})


@require_GET
def download(request, pk):
    document = get_object_or_404(FullDocument.objects.select_related("project", "file"), pk=pk)
    try:
        data = services.download(document, by=request.user, request=request)
    except PermissionDenied as exc:
        return deny_access(request, str(exc))
    except IntegrityFailure as failure:
        record_integrity_failure(failure, request=request)
        return render(request, "files/integrity_failed.html", {"stored": document.file}, status=409)
    response = HttpResponse(data, content_type="application/pdf")
    response["Content-Disposition"] = content_disposition_header(
        as_attachment=True, filename=document.file.original_name
    )
    return response
