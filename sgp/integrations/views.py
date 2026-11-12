"""Fila, reprocessamento, exportação, mapeamento e consulta de produto (rotas-ui.md da 012)."""

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import content_disposition_header
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from sgp.accounts.profiles import deny_access

from . import mapping, sankhya, services
from .models import IntegrationMessage, MessageStatus

IT_ONLY = "só a TI (Administrador do sistema) cuida da integração"


@require_GET
def queue(request):
    if not services.is_it(request.user):
        return deny_access(request, IT_ONLY)
    queryset = IntegrationMessage.objects.select_related("project")
    status = request.GET.get("situacao", "")
    record_type = request.GET.get("registro", "")
    if status in MessageStatus.values:
        queryset = queryset.filter(status=status)
    if record_type in mapping.RECORD_FIELDS:
        queryset = queryset.filter(record_type=record_type)
    page = Paginator(queryset, 50).get_page(request.GET.get("pagina"))
    context = {
        "page": page,
        "statuses": MessageStatus.choices,
        "records": list(mapping.RECORD_LABELS.items()),
        "status": status,
        "record_type": record_type,
        "configured": sankhya.configured(),
        "mapping": services.current_mapping(),
    }
    return render(request, "integrations/queue.html", context)


@require_POST
def reprocess(request, pk):
    if not services.is_it(request.user):
        return deny_access(request, IT_ONLY)
    message = get_object_or_404(IntegrationMessage, pk=pk)
    try:
        result = services.reprocess(message, by=request.user)
    except ValidationError as exc:
        for text in exc.messages:
            messages.error(request, text)
    else:
        messages.success(request, f"Mensagem reprocessada: {result.get_status_display()}.")
    return redirect("integrations:queue")


@require_GET
def export(request):
    if not services.is_it(request.user):
        return deny_access(request, IT_ONLY)
    try:
        name, content_type, data = services.export(
            request.GET.get("registro", ""),
            request.GET.get("formato", ""),
            by=request.user,
            request=request,
        )
    except ValidationError as exc:
        for text in exc.messages:
            messages.error(request, text)
        return redirect("integrations:queue")
    response = HttpResponse(data, content_type=content_type)
    response["Content-Disposition"] = content_disposition_header(as_attachment=True, filename=name)
    return response


@require_http_methods(["GET", "POST"])
def mapping_view(request):
    if not services.is_it(request.user):
        return deny_access(request, IT_ONLY)
    current = services.current_mapping()
    text = current.yaml
    if request.method == "POST":
        text = request.POST.get("yaml", "")
        try:
            record = services.publish_mapping(
                by=request.user, text=text, note=request.POST.get("observacao", "")
            )
        except (ValidationError, PermissionDenied) as exc:
            for message in getattr(exc, "messages", [str(exc)]):
                messages.error(request, message)
        else:
            messages.success(request, f"Mapeamento versão {record.version} publicado.")
            return redirect("integrations:mapping")
    return render(request, "integrations/mapping.html", {"current": current, "text": text})


@require_GET
def product(request):
    code = request.GET.get("codigo", "")
    context = {"code": code}
    try:
        context["product"] = services.lookup_product(code)
    except ValidationError as exc:
        context["warning"] = " ".join(exc.messages)
    except services.ProductNotFound:
        context["warning"] = f"Código {code} não encontrado no cadastro de produtos do Sankhya."
    except sankhya.SankhyaError as exc:
        context["warning"] = (
            f"Código não conferido no Sankhya: {exc} O cadastro continua normalmente."
        )
    return render(request, "integrations/_product.html", context)
