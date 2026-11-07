"""Pessoa sem perfil só acessa "Solicitar acesso" e o logout (FR-003, FR-015)."""

from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect

from .profiles import active_profiles

NO_PROFILE_MESSAGE = "Você ainda não tem perfil no SGP-P&D. Solicite acesso abaixo."


class ProfileRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            return None
        if not getattr(view_func, "login_required", True):
            return None
        if not user.is_active:
            logout(request)
            messages.error(request, "Sua conta está desativada no SGP-P&D.")
            return redirect("accounts:login")
        if getattr(view_func, "sgp_allow_without_profile", False):
            return None
        if active_profiles(user):
            return None
        from sgp.audit.services import record_event

        record_event(
            "auth.permission_denied",
            actor=user,
            object_type="route",
            object_id=request.path[:64],
            object_repr=request.path[:255],
            new_value={
                "rota": request.path,
                "metodo": request.method,
                "motivo": "pessoa sem perfil ativo",
            },
        )
        messages.warning(request, NO_PROFILE_MESSAGE)
        return redirect("accounts:access_request")
