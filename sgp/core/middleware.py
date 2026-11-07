"""Encerramento de sessão por inatividade (FR-005 da feature 001)."""

from datetime import UTC, datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import redirect_to_login
from django.utils import timezone

LAST_ACTIVITY_KEY = "sgp_ultimo_acesso"
EXPIRED_MESSAGE = "Sua sessão expirou por inatividade. Entre novamente."


class InactivityTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            now = timezone.now().timestamp()
            last = request.session.get(LAST_ACTIVITY_KEY)
            limit = settings.SESSION_IDLE_TIMEOUT_MINUTES * 60
            if last is not None and now - float(last) > limit:
                return self._expire(request, user, float(last))
            request.session[LAST_ACTIVITY_KEY] = now
        return self.get_response(request)

    def _expire(self, request, user, last):
        from sgp.audit.services import record_event

        last_dt = datetime.fromtimestamp(last, tz=UTC)
        record_event(
            "auth.session_expired",
            actor=user,
            obj=user,
            old_value={"ultimo_acesso": last_dt},
            reason=f"Inatividade acima de {settings.SESSION_IDLE_TIMEOUT_MINUTES} minutos",
        )
        logout(request)
        messages.warning(request, EXPIRED_MESSAGE)
        return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)
