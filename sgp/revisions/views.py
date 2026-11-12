"""Telas da revisão controlada de modelos (contrato rotas-ui.md da feature 013)."""

import datetime

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from sgp.accounts.profiles import Profile, active_profiles, profile_required

from . import services
from .adapters import load
from .models import RetirementStatus, TemplateRetirement


def _errors(request, exc: ValidationError) -> None:
    for message in exc.messages:
        messages.error(request, message)


@require_GET
def revision_list(request):
    profiles = active_profiles(request.user)
    context = {
        "reviews": services.pending_reviews(),
        "retirements": TemplateRetirement.objects.filter(
            status=RetirementStatus.REQUESTED
        ).select_related("subdocument_type", "requested_by"),
        "is_manager": Profile.RD_MANAGER in profiles,
        "is_quality": Profile.QUALITY in profiles,
    }
    return render(request, "revisions/list.html", context)


@require_POST
@profile_required(Profile.QUALITY)
def submit(request, kind, pk):
    adapter, obj = load(kind, pk)
    try:
        services.submit(
            kind,
            obj,
            by=request.user,
            reason=request.POST.get("motivo", ""),
            impact=request.POST.get("impacto", ""),
            request=request,
        )
    except ValidationError as exc:
        _errors(request, exc)
        return redirect(adapter.edit_url(obj))
    messages.success(request, "Revisão enviada para aprovação do Gestor de P&D.")
    return redirect("revisions:list")


@require_POST
@profile_required(Profile.RD_MANAGER)
def return_revision(request, kind, pk):
    _adapter, obj = load(kind, pk)
    try:
        services.return_revision(
            kind, obj, by=request.user, comment=request.POST.get("comentario", ""), request=request
        )
    except ValidationError as exc:
        _errors(request, exc)
        return redirect("revisions:approve", kind=kind, pk=pk)
    messages.success(request, "Revisão devolvida para a Qualidade/AR com o comentário.")
    return redirect("revisions:list")


def _valid_from(request):
    if request.POST.get("vigencia", "imediata") == "imediata":
        return None
    try:
        return datetime.date.fromisoformat(request.POST.get("data_vigencia", ""))
    except ValueError:
        raise ValidationError("Informe a data de início da vigência.") from None


@require_http_methods(["GET", "POST"])
@profile_required(Profile.RD_MANAGER)
def approve(request, kind, pk):
    adapter, obj = load(kind, pk)
    if request.method == "POST":
        try:
            services.approve(
                kind,
                obj,
                by=request.user,
                password=request.POST.get("senha", ""),
                valid_from=_valid_from(request),
                request=request,
            )
        except ValidationError as exc:
            _errors(request, exc)
            return redirect("revisions:approve", kind=kind, pk=pk)
        messages.success(request, "Revisão aprovada com assinatura e publicada.")
        return redirect("revisions:history", kind=kind, pk=pk)
    baseline = services.baseline(adapter, obj)
    context = {
        "kind": kind,
        "adapter": adapter,
        "obj": obj,
        "family": adapter.family_label(obj),
        "baseline": baseline,
        "diff": services.compare(adapter, baseline, obj),
        "problems": adapter.errors(obj),
    }
    return render(request, "revisions/approve.html", context)


@require_POST
@profile_required(Profile.QUALITY)
def discard(request, kind, pk):
    adapter, obj = load(kind, pk)
    try:
        services.discard(
            kind, obj, by=request.user, reason=request.POST.get("motivo", ""), request=request
        )
    except ValidationError as exc:
        _errors(request, exc)
        return redirect(adapter.edit_url(obj))
    messages.success(request, "Revisão descartada; ela continua no histórico.")
    return redirect("revisions:history", kind=kind, pk=pk)


@require_POST
@profile_required(Profile.QUALITY, Profile.RD_MANAGER)
def verify(request, kind, pk):
    adapter, obj = load(kind, pk)
    try:
        result = services.verify(kind, obj, by=request.user, request=request)
    except ValidationError as exc:
        _errors(request, exc)
    else:
        if result["integro"]:
            messages.success(request, "Versão íntegra: o conteúdo confere com o aprovado.")
        for problem in result["problemas"]:
            messages.error(request, problem)
    return redirect("revisions:history", kind=kind, pk=pk)


@require_GET
def history(request, kind, pk):
    adapter, obj = load(kind, pk)
    profiles = active_profiles(request.user)
    context = {
        "kind": kind,
        "adapter": adapter,
        "obj": obj,
        "family": adapter.family_label(obj),
        "detail_url": adapter.detail_url(obj),
        "rows": services.history(kind, obj),
        "can_verify": bool({Profile.QUALITY, Profile.RD_MANAGER} & profiles),
    }
    return render(request, "revisions/history.html", context)


@require_GET
def compare(request, kind, pk):
    adapter, obj = load(kind, pk)
    versions = list(adapter.versions(obj))
    other_pk = request.GET.get("com")
    other = next((v for v in versions if str(v.pk) == str(other_pk)), None)
    other = other or services.baseline(adapter, obj)
    older, newer = sorted([other, obj], key=lambda v: adapter.version(v)) if other else (None, obj)
    context = {
        "kind": kind,
        "adapter": adapter,
        "obj": obj,
        "family": adapter.family_label(obj),
        "versions": versions,
        "older": older,
        "newer": newer,
        "other_pk": other.pk if other else None,
        "diff": services.compare(adapter, older, newer),
    }
    return render(request, "revisions/compare.html", context)


@require_POST
@profile_required(Profile.QUALITY)
def retirement_request(request, pk):
    _adapter, template = load("form", pk)
    try:
        services.request_retirement(
            template, by=request.user, reason=request.POST.get("motivo", ""), request=request
        )
    except ValidationError as exc:
        _errors(request, exc)
        return redirect("formtemplates:detail", pk=pk)
    messages.success(request, "Retirada de uso pedida; aguarda a decisão do Gestor de P&D.")
    return redirect("revisions:list")


@require_POST
@profile_required(Profile.RD_MANAGER)
def retirement_approve(request, pk):
    retirement = get_object_or_404(TemplateRetirement, pk=pk)
    try:
        services.approve_retirement(
            retirement, by=request.user, password=request.POST.get("senha", ""), request=request
        )
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(request, "Retirada de uso aprovada com assinatura.")
    return redirect("revisions:list")


@require_POST
@profile_required(Profile.RD_MANAGER)
def retirement_return(request, pk):
    retirement = get_object_or_404(TemplateRetirement, pk=pk)
    try:
        services.return_retirement(
            retirement, by=request.user, comment=request.POST.get("comentario", ""), request=request
        )
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(request, "Pedido de retirada devolvido com o comentário.")
    return redirect("revisions:list")
