"""Administração: pessoas e perfis, solicitações de acesso e bloqueios (histórias 2 e 5)."""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .forms import (
    DecisionForm,
    GrantProfileForm,
    PeopleSearchForm,
    ReasonForm,
    RevokeProfileForm,
)
from .models import AccessRequest, LoginLockout, ProfileAssignment, User
from .profiles import EXPECTED_APPROVER, Profile, profile_required
from .services import (
    decide_access_request,
    grant_profile,
    release_lockout,
    revoke_profile,
    set_person_active,
)


def _errors(request, exc: ValidationError) -> None:
    messages.error(request, " ".join(exc.messages))


@require_GET
@profile_required(Profile.ADMIN)
def people_list(request):
    form = PeopleSearchForm(request.GET or None)
    people = User.objects.prefetch_related(
        Prefetch(
            "profile_assignments",
            queryset=ProfileAssignment.objects.filter(revoked_at__isnull=True),
            to_attr="active_assignments",
        )
    )
    if form.is_valid() and form.cleaned_data["q"]:
        term = form.cleaned_data["q"]
        people = people.filter(Q(username__icontains=term) | Q(full_name__icontains=term))
    return render(request, "accounts/people_list.html", {"form": form, "people": people[:200]})


@require_GET
@profile_required(Profile.ADMIN)
def person_detail(request, user_id):
    person = get_object_or_404(User, pk=user_id)
    assignments = ProfileAssignment.objects.filter(user=person).select_related(
        "granted_by", "revoked_by"
    )
    active_codes = [a.profile for a in assignments if a.revoked_at is None]
    context = {
        "person": person,
        "assignments": assignments,
        "active": [a for a in assignments if a.revoked_at is None],
        "grant_form": GrantProfileForm(unavailable=active_codes),
        "revoke_form": RevokeProfileForm(),
        "status_form": ReasonForm(),
        "approvers": {Profile(code).label: who for code, who in EXPECTED_APPROVER.items()},
    }
    return render(request, "accounts/person_detail.html", context)


@require_POST
@profile_required(Profile.ADMIN)
def grant_profile_view(request, user_id):
    person = get_object_or_404(User, pk=user_id)
    form = GrantProfileForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Preencha perfil, motivo e referência da aprovação.")
        return redirect("accounts:person_detail", user_id=person.pk)
    try:
        grant_profile(
            person,
            form.cleaned_data["profile"],
            by=request.user,
            reason=form.cleaned_data["reason"],
            approval_reference=form.cleaned_data["approval_reference"],
        )
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(
            request, f"Perfil {Profile(form.cleaned_data['profile']).label} concedido."
        )
    return redirect("accounts:person_detail", user_id=person.pk)


@require_POST
@profile_required(Profile.ADMIN)
def revoke_profile_view(request, user_id, assignment_id):
    assignment = get_object_or_404(ProfileAssignment, pk=assignment_id, user_id=user_id)
    form = RevokeProfileForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Informe o motivo e a referência da aprovação da revogação.")
        return redirect("accounts:person_detail", user_id=user_id)
    try:
        revoke_profile(
            assignment,
            by=request.user,
            reason=form.cleaned_data["reason"],
            approval_reference=form.cleaned_data["approval_reference"],
        )
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(request, f"Perfil {assignment.get_profile_display()} revogado.")
    return redirect("accounts:person_detail", user_id=user_id)


@require_POST
@profile_required(Profile.ADMIN)
def deactivate_person_view(request, user_id):
    return _set_active(request, user_id, active=False)


@require_POST
@profile_required(Profile.ADMIN)
def reactivate_person_view(request, user_id):
    return _set_active(request, user_id, active=True)


def _set_active(request, user_id, *, active: bool):
    person = get_object_or_404(User, pk=user_id)
    form = ReasonForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Informe o motivo.")
        return redirect("accounts:person_detail", user_id=person.pk)
    try:
        set_person_active(
            person, by=request.user, active=active, reason=form.cleaned_data["reason"]
        )
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(request, "Pessoa reativada." if active else "Pessoa desativada.")
    return redirect("accounts:person_detail", user_id=person.pk)


@require_GET
@profile_required(Profile.ADMIN)
def access_requests_list(request):
    pending = AccessRequest.objects.filter(status=AccessRequest.Status.PENDING).select_related(
        "user"
    )
    decided = (
        AccessRequest.objects.exclude(status=AccessRequest.Status.PENDING)
        .select_related("user", "decided_by")
        .order_by("-decided_at")[:50]
    )
    context = {"pending": pending, "decided": decided, "decision_form": DecisionForm()}
    return render(request, "accounts/access_requests.html", context)


@require_POST
@profile_required(Profile.ADMIN)
def decide_access_request_view(request, request_id):
    access_request = get_object_or_404(AccessRequest, pk=request_id)
    form = DecisionForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Escolha a decisão e informe o motivo.")
        return redirect("accounts:access_requests")
    try:
        decide_access_request(
            access_request,
            by=request.user,
            decision=form.cleaned_data["decision"],
            reason=form.cleaned_data["reason"],
        )
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(request, "Decisão registrada.")
    return redirect("accounts:access_requests")


@require_GET
@profile_required(Profile.ADMIN)
def lockouts_list(request):
    active = LoginLockout.objects.filter(released_at__isnull=True, expires_at__gt=timezone.now())
    recent = LoginLockout.objects.select_related("released_by")[:50]
    return render(
        request,
        "accounts/lockouts.html",
        {"active": active, "recent": recent, "release_form": ReasonForm()},
    )


@require_POST
@profile_required(Profile.ADMIN)
def release_lockout_view(request, lockout_id):
    lockout = get_object_or_404(LoginLockout, pk=lockout_id)
    form = ReasonForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Informe o motivo do desbloqueio.")
        return redirect("accounts:lockouts")
    try:
        release_lockout(lockout, by=request.user, reason=form.cleaned_data["reason"])
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(request, f"Login {lockout.username} desbloqueado.")
    return redirect("accounts:lockouts")
