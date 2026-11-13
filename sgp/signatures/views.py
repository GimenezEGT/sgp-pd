"""Telas do ciclo de revisão e assinatura (contrato rotas-ui.md da feature 005)."""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from sgp.accounts.profiles import Profile, active_profiles, deny_access, profile_required
from sgp.core.access import can_access_project

from . import services
from .documents import IN_REVIEW, STATUS_LABELS, load
from .forms import DelegationForm, EndDelegationForm
from .models import ApprovalDelegation, ApprovedVersion, DocumentKind, ReviewComment


def _errors(request, exc: ValidationError) -> None:
    for message in exc.messages:
        messages.error(request, message)


def _document(request, kind, pk):
    adapter, obj = load(kind, pk)
    if not can_access_project(request.user, adapter.project(obj)):
        return adapter, obj, deny_access(request, "sem acesso ao projeto do documento")
    return adapter, obj, None


def _context(request, adapter, obj, **extra):
    from .canonical import content_hash

    return {
        "adapter": adapter,
        "obj": obj,
        "kind": adapter.kind,
        "title": adapter.title(obj),
        "status": adapter.status(obj),
        "status_label": STATUS_LABELS.get(adapter.status(obj), adapter.status(obj)),
        "approver": services.is_approver(request.user),
        "own_submission": services.own_submission(request.user, adapter, obj),
        "can_delegate": Profile.RD_MANAGER in active_profiles(request.user),
        "version": adapter.version(obj),
        "digest": content_hash(adapter.snapshot(obj)),
        "signatures": services.signatures_of(adapter, obj),
        "comments": ReviewComment.objects.filter(
            kind=adapter.kind, object_id=obj.pk
        ).select_related("author"),
        "versions": services.versions_of(adapter, obj),
        "back_url": adapter.url(obj),
        **extra,
    }


@require_http_methods(["GET", "POST"])
def submit_view(request, kind, pk):
    adapter, obj, denied = _document(request, kind, pk)
    if denied:
        return denied
    if request.method == "POST":
        try:
            services.submit(
                kind, obj, by=request.user, password=request.POST.get("senha", ""), request=request
            )
        except ValidationError as exc:
            _errors(request, exc)
        else:
            messages.success(request, "Documento enviado para revisão e assinado como Elaborado.")
            return redirect(adapter.url(obj))
    context = _context(request, adapter, obj, action="enviar", missing=adapter.completeness(obj))
    return render(request, "signatures/sign.html", context)


@require_http_methods(["GET", "POST"])
def approve_view(request, kind, pk):
    adapter, obj, denied = _document(request, kind, pk)
    if denied:
        return denied
    if not services.is_approver(request.user):
        return deny_access(request, "aprovação exige Gestor de P&D ou delegação vigente")
    if request.method == "POST":
        try:
            services.approve(
                kind, obj, by=request.user, password=request.POST.get("senha", ""), request=request
            )
        except ValidationError as exc:
            _errors(request, exc)
        else:
            messages.success(request, "Documento aprovado e assinado; a versão foi congelada.")
            return redirect(adapter.url(obj))
    return render(
        request, "signatures/sign.html", _context(request, adapter, obj, action="aprovar")
    )


@require_POST
def return_view(request, kind, pk):
    adapter, obj, denied = _document(request, kind, pk)
    if denied:
        return denied
    try:
        services.return_document(
            kind, obj, by=request.user, comment=request.POST.get("comentario", "")
        )
    except ValidationError as exc:
        _errors(request, exc)
        return redirect("signatures:approve", kind=kind, pk=pk)
    messages.success(request, "Documento devolvido com o comentário registrado.")
    return redirect(adapter.url(obj))


@require_POST
def review_view(request, kind, pk):
    adapter, obj, denied = _document(request, kind, pk)
    if denied:
        return denied
    try:
        services.sign_review(
            kind, obj, by=request.user, password=request.POST.get("senha", ""), request=request
        )
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(request, "Assinatura de revisão registrada.")
    return redirect(adapter.url(obj))


@require_POST
def new_version_view(request, kind, pk):
    adapter, obj, denied = _document(request, kind, pk)
    if denied:
        return denied
    try:
        services.new_version(kind, obj, by=request.user, reason=request.POST.get("motivo", ""))
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(
            request, f"Versão {adapter.version(adapter.get(obj.pk)):02d} criada em rascunho."
        )
    return redirect(adapter.url(obj))


@require_POST
def verify_view(request, kind, pk):
    adapter, obj, denied = _document(request, kind, pk)
    if denied:
        return denied
    result = services.verify(kind, obj, by=request.user)
    if result["integro"]:
        messages.success(
            request, f"Íntegro: {result['versoes']} versão(ões) aprovada(s) conferida(s)."
        )
    else:
        for problem in result["problemas"]:
            messages.error(request, f"Divergência: {problem}")
    return redirect(adapter.url(obj))


@require_GET
def version_view(request, kind, pk, version):
    adapter, obj, denied = _document(request, kind, pk)
    if denied:
        return denied
    approved = get_object_or_404(ApprovedVersion, kind=kind, object_id=obj.pk, version=version)
    content = approved.content
    if kind == DocumentKind.BUSINESS_PLAN:
        from sgp.projects.permissions import FINANCIAL_FIELDS, can_view_financials

        if not can_view_financials(request.user, adapter.project(obj)):
            content = dict(content)
            content["plano"] = {
                key: ("[restrito]" if key in FINANCIAL_FIELDS else value)
                for key, value in content.get("plano", {}).items()
            }
            content["previsoes"] = "[restrito]"
            content["total"] = "[restrito]"
    superseded = ApprovedVersion.objects.filter(
        kind=kind, object_id=obj.pk, version__gt=version
    ).exists() or (adapter.version(obj) != version)
    context = _context(
        request,
        adapter,
        obj,
        approved=approved,
        content=content,
        superseded=superseded,
        version_signatures=services.signatures_of(adapter, obj, version=version),
    )
    return render(request, "signatures/version.html", context)


@require_GET
def queue_view(request):
    if not services.is_approver(request.user):
        return deny_access(request, "fila de revisão exige Gestor de P&D ou delegação vigente")
    rows = services.review_queue(request.user)
    own_rows = services.review_queue(request.user, own=True)
    return render(
        request,
        "signatures/queue.html",
        {"rows": rows, "own_rows": own_rows, "in_review": IN_REVIEW},
    )


@require_http_methods(["GET", "POST"])
@profile_required(Profile.RD_MANAGER)
def delegations_view(request):
    form = DelegationForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        try:
            services.create_delegation(by=request.user, **form.cleaned_data)
        except ValidationError as exc:
            _errors(request, exc)
        else:
            messages.success(request, "Delegação de aprovação registrada.")
            return redirect("signatures:delegations")
    delegations = ApprovalDelegation.objects.select_related("delegator", "delegate", "ended_by")
    today = timezone.localdate()
    return render(
        request,
        "signatures/delegations.html",
        {"form": form, "delegations": delegations, "today": today, "end_form": EndDelegationForm()},
    )


@require_POST
@profile_required(Profile.RD_MANAGER)
def delegation_end_view(request, pk):
    delegation = get_object_or_404(ApprovalDelegation, pk=pk)
    form = EndDelegationForm(request.POST)
    try:
        if not form.is_valid():
            raise ValidationError("Informe o motivo do encerramento.")
        services.end_delegation(delegation, by=request.user, reason=form.cleaned_data["reason"])
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(request, "Delegação encerrada.")
    return redirect("signatures:delegations")
