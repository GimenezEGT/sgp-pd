"""Telas do dossiê técnico (contrato rotas-ui.md da feature 011)."""

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.utils.http import content_disposition_header
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from sgp.accounts.profiles import deny_access
from sgp.core.access import can_access_project
from sgp.files.storage import IntegrityFailure, record_integrity_failure
from sgp.projects.models import Project

from . import definition, services
from .models import (
    COMPANY_DEFAULTS,
    DossierSupplement,
    DossierVersion,
    StandardText,
    Submission,
    SubmissionResult,
    TextStatus,
)


def _errors(request, exc):
    for message in exc.messages:
        messages.error(request, message)


@require_http_methods(["GET", "POST"])
def project_dossier(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if not can_access_project(request.user, project):
        return deny_access(request, "sem acesso ao projeto")
    if request.method == "POST":
        try:
            version = services.generate(project, by=request.user)
        except PermissionDenied as exc:
            return deny_access(request, str(exc))
        except ValidationError as exc:
            _errors(request, exc)
        else:
            kind = "final" if version.final else "rascunho (há itens faltando)"
            messages.success(request, f"Dossiê versão {version.number:02d} gerado: {kind}.")
        return redirect("dossier:project", project_id=project.pk)
    try:
        result = services.checklist(project)
    except ValidationError as exc:
        _errors(request, exc)
        result = None
    history = list(services.versions(project).prefetch_related("submissions"))
    context = {
        "project": project,
        "result": result,
        "versions": history,
        "is_quality": services.is_quality(request.user),
        "results": [(code, label) for code, label in SubmissionResult.choices if code != "pending"],
    }
    return render(request, "dossier/project.html", context)


@require_http_methods(["GET", "POST"])
def supplement(request, project_id, item_key):
    project = get_object_or_404(Project, pk=project_id)
    if not can_access_project(request.user, project):
        return deny_access(request, "sem acesso ao projeto")
    if not services.is_quality(request.user):
        return deny_access(request, services.QUALITY_ONLY)
    leaves = {
        item["key"]: (item, parents)
        for item, parents in definition.leaves(services.current_definition().parsed["itens"])
    }
    if item_key not in leaves:
        return redirect("dossier:project", project_id=project.pk)
    record = DossierSupplement.objects.filter(project=project, item_key=item_key).first()
    if request.method == "POST":
        try:
            services.save_supplement(
                project,
                by=request.user,
                item_key=item_key,
                text=request.POST.get("texto", ""),
                not_applicable=request.POST.get("nao_aplicavel") == "1",
                justification=request.POST.get("justificativa", ""),
            )
        except ValidationError as exc:
            _errors(request, exc)
        else:
            messages.success(request, f"Complemento do item {item_key} gravado.")
            return redirect("dossier:project", project_id=project.pk)
    item, parents = leaves[item_key]
    label = " › ".join(f"{node['numero']}. {node['titulo']}" for node in (*parents, item))
    return render(
        request,
        "dossier/supplement.html",
        {"project": project, "item_key": item_key, "label": label, "record": record},
    )


@require_GET
def download(request, pk, kind):
    version = get_object_or_404(DossierVersion.objects.select_related("project"), pk=pk)
    try:
        stored, data = services.download(version, kind, by=request.user, request=request)
    except PermissionDenied as exc:
        return deny_access(request, str(exc))
    except ValidationError:
        return redirect("dossier:project", project_id=version.project_id)
    except IntegrityFailure as failure:
        record_integrity_failure(failure, request=request)
        return render(
            request, "files/integrity_failed.html", {"stored": failure.stored}, status=409
        )
    response = HttpResponse(data, content_type=stored.content_type)
    response["Content-Disposition"] = content_disposition_header(
        as_attachment=True, filename=stored.original_name
    )
    return response


@require_POST
def submit(request, pk):
    version = get_object_or_404(DossierVersion.objects.select_related("project"), pk=pk)
    if not can_access_project(request.user, version.project) or not services.is_quality(
        request.user
    ):
        return deny_access(request, services.QUALITY_ONLY)
    try:
        services.submit(
            version,
            by=request.user,
            protocol=request.POST.get("protocolo", ""),
            submitted_on=parse_date(request.POST.get("data", "") or ""),
            signed_pdf=request.FILES.get("pdf_assinado"),
        )
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(request, "Envio registrado.")
    return redirect("dossier:project", project_id=version.project_id)


@require_POST
def result(request, pk):
    submission = get_object_or_404(Submission.objects.select_related("version__project"), pk=pk)
    project = submission.version.project
    if not can_access_project(request.user, project) or not services.is_quality(request.user):
        return deny_access(request, services.QUALITY_ONLY)
    try:
        services.record_result(
            submission,
            by=request.user,
            result=request.POST.get("resultado", ""),
            result_on=parse_date(request.POST.get("data", "") or ""),
            notes=request.POST.get("observacoes", ""),
        )
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(request, "Resultado registrado.")
    return redirect("dossier:project", project_id=project.pk)


@require_GET
def addendum(request, pk):
    version = get_object_or_404(DossierVersion.objects.select_related("project"), pk=pk)
    try:
        previous, changes, data = services.addendum(
            version, by=request.user, request=request, as_pdf=request.GET.get("pdf") == "1"
        )
    except PermissionDenied as exc:
        return deny_access(request, str(exc))
    if data is not None:
        response = HttpResponse(data, content_type="application/pdf")
        name = f"Aditamento {version.subject} v{version.number:02d}.pdf"
        response["Content-Disposition"] = content_disposition_header(
            as_attachment=True, filename=name
        )
        return response
    return render(
        request,
        "dossier/addendum.html",
        {"version": version, "previous": previous, "changes": changes},
    )


@require_http_methods(["GET", "POST"])
def texts(request):
    if request.method == "POST":
        if not services.is_quality(request.user):
            return deny_access(request, services.QUALITY_ONLY)
        try:
            record = services.save_text(
                by=request.user,
                key=request.POST.get("chave", ""),
                title=request.POST.get("titulo", ""),
                text=request.POST.get("texto", ""),
            )
        except ValidationError as exc:
            _errors(request, exc)
        else:
            messages.success(
                request, f"Texto {record.key} versão {record.version} gravado; falta a aprovação."
            )
        return redirect("dossier:texts")
    rows = StandardText.objects.select_related("created_by", "approved_by").order_by(
        "key", "-version"
    )
    return render(
        request,
        "dossier/texts.html",
        {"rows": rows, "is_quality": services.is_quality(request.user), "draft": TextStatus.DRAFT},
    )


@require_POST
def text_approve(request, pk):
    if not (services.is_quality(request.user) or services.is_manager(request.user)):
        return deny_access(request, "só a Qualidade/AR ou o Gestor de P&D aprova textos padrão")
    record = get_object_or_404(StandardText, pk=pk)
    try:
        services.approve_text(
            record, by=request.user, password=request.POST.get("senha", ""), request=request
        )
    except PermissionDenied as exc:
        return deny_access(request, str(exc))
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(request, f"Texto {record.key} versão {record.version} aprovado.")
    return redirect("dossier:texts")


@require_http_methods(["GET", "POST"])
def definition_view(request):
    current = services.current_definition()
    text = current.yaml
    if request.method == "POST":
        if not services.is_quality(request.user):
            return deny_access(request, services.QUALITY_ONLY)
        text = request.POST.get("yaml", "")
        try:
            record = services.publish_definition(
                by=request.user, text=text, note=request.POST.get("observacao", "")
            )
        except ValidationError as exc:
            _errors(request, exc)
        else:
            messages.success(request, f"Definição versão {record.version} publicada.")
            return redirect("dossier:definition")
    return render(
        request,
        "dossier/definition.html",
        {"current": current, "text": text, "is_quality": services.is_quality(request.user)},
    )


@require_http_methods(["GET", "POST"])
def company_view(request):
    current = services.company()
    values = (
        {name: getattr(current, name) for name in services.COMPANY_FIELDS}
        if current
        else dict(COMPANY_DEFAULTS)
    )
    if request.method == "POST":
        if not services.is_quality(request.user):
            return deny_access(request, services.QUALITY_ONLY)
        values = {name: request.POST.get(name, "") for name in services.COMPANY_FIELDS}
        try:
            services.save_company(by=request.user, data=values)
        except ValidationError as exc:
            _errors(request, exc)
        else:
            messages.success(request, "Dados da empresa e do responsável técnico e legal gravados.")
            return redirect("dossier:company")
    return render(
        request,
        "dossier/company.html",
        {"values": values, "is_quality": services.is_quality(request.user)},
    )
