"""Consulta, exportação e verificação de integridade da trilha (histórias 3 e 4)."""

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Max
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from sgp.accounts.profiles import AUDIT_TRAIL_PROFILES, INTEGRITY_PROFILES, profile_required

from . import exports
from .forms import AuditFilterForm
from .models import AuditEvent, ChainVerification
from .presentation import EventPresenter
from .services import latest_verification, record_event
from .tasks import verify_chain_manual


def _filtered(request):
    form = AuditFilterForm(request.GET or None)
    queryset = AuditEvent.objects.order_by("seq")
    if form.is_bound and form.is_valid():
        queryset = form.apply(queryset)
    elif not form.is_bound:
        form = AuditFilterForm({})
        form.is_valid()
    else:
        queryset = queryset.none()
    return form, queryset


@require_GET
@profile_required(*AUDIT_TRAIL_PROFILES)
def trail(request):
    form, queryset = _filtered(request)
    page = Paginator(queryset, settings.AUDIT_PAGE_SIZE).get_page(request.GET.get("pagina"))
    EventPresenter(request.user).decorate(page.object_list)
    query = request.GET.copy()
    query.pop("pagina", None)
    context = {"form": form, "page": page, "query": query.urlencode()}
    if request.headers.get("HX-Request") == "true":
        return render(request, "audit/_trail_table.html", context)
    return render(request, "audit/trail.html", context)


@require_GET
@profile_required(*AUDIT_TRAIL_PROFILES)
def export(request):
    form, queryset = _filtered(request)
    fmt = request.GET.get("formato", "csv")
    if fmt not in {"csv", "xlsx"} or not form.is_valid():
        messages.error(request, "Filtros ou formato de exportação inválidos.")
        return redirect("audit:trail")
    # Fixa o recorte antes de registrar a exportação, para o arquivo conter exatamente
    # os eventos contados (o próprio evento de exportação fica fora do arquivo).
    upper = queryset.aggregate(value=Max("seq"))["value"] or 0
    queryset = queryset.filter(seq__lte=upper)
    count = queryset.count()
    exported_at = timezone.now()
    record_event(
        "audit.exported",
        new_value={"formato": fmt, "filtros": form.as_event_value(), "eventos": count},
    )
    builder = exports.csv_response if fmt == "csv" else exports.xlsx_response
    return builder(
        queryset,
        exported_by=request.user,
        filters=form.describe(),
        count=count,
        exported_at=exported_at,
    )


@require_GET
@profile_required(*INTEGRITY_PROFILES)
def integrity(request):
    verifications = ChainVerification.objects.select_related("triggered_by")
    page = Paginator(verifications, 20).get_page(request.GET.get("pagina"))
    return render(
        request,
        "audit/integrity.html",
        {"latest": latest_verification(), "page": page},
    )


@require_POST
@profile_required(*INTEGRITY_PROFILES)
def verify_now(request):
    try:
        verify_chain_manual.delay(request.user.pk)
    except Exception:  # noqa: BLE001 - fila indisponível não pode virar erro 500
        messages.error(request, "Não foi possível enfileirar a verificação. Tente novamente.")
    else:
        messages.success(
            request,
            "Verificação solicitada. O resultado aparece nesta página quando terminar.",
        )
    return redirect("audit:integrity")
