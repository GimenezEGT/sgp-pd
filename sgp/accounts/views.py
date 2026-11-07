"""Login, logout e solicitação de acesso (história 1 da feature 001)."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_not_required
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST

from sgp.audit.services import record_event

from .forms import AccessRequestForm, LoginForm
from .models import AccessRequest
from .profiles import active_profiles, allow_without_profile
from .services import create_access_request, login_flow


@login_not_required
@never_cache
@sensitive_post_parameters("password")
def login_view(request):
    if request.method == "GET" and request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    form = LoginForm(request.POST or None)
    next_url = request.POST.get("next") or request.GET.get("next") or ""
    error = ""
    if request.method == "POST" and form.is_valid():
        result = login_flow(request, form.cleaned_data["username"], form.cleaned_data["password"])
        if result.status == "success":
            if not result.has_profile:
                return redirect("accounts:access_request")
            if next_url and url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
            ):
                return redirect(next_url)
            return redirect(settings.LOGIN_REDIRECT_URL)
        error = result.message
    return render(request, "accounts/login.html", {"form": form, "error": error, "next": next_url})


@require_POST
@allow_without_profile
def logout_view(request):
    user = request.user
    record_event("auth.logout", actor=user, obj=user)
    logout(request)
    messages.info(request, "Você saiu do SGP-P&D.")
    return redirect("accounts:login")


@never_cache
@allow_without_profile
def access_request_view(request):
    form = AccessRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            create_access_request(request.user, form.cleaned_data["justification"])
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
        else:
            messages.success(
                request, "Solicitação registrada. O Administrador do sistema vai analisá-la."
            )
            return redirect("accounts:access_request")
    context = {
        "form": form,
        "instructions": settings.ACCESS_REQUEST_INSTRUCTIONS,
        "own_requests": AccessRequest.objects.filter(user=request.user)[:20],
        "has_profile": bool(active_profiles(request.user)),
    }
    return render(request, "accounts/access_request.html", context)
