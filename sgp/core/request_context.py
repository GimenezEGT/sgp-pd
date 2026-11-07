"""Contexto da requisição em andamento (origem e usuário) para a trilha de auditoria."""

import contextvars

from django.conf import settings

_current_request: contextvars.ContextVar = contextvars.ContextVar("sgp_request", default=None)


def current_request():
    return _current_request.get()


def client_ip(request) -> str:
    if request is None:
        return ""
    header = getattr(settings, "SGP_CLIENT_IP_HEADER", "")
    value = request.META.get(header, "") if header else ""
    if not value:
        value = request.META.get("REMOTE_ADDR", "")
    return value.split(",")[0].strip()[:45]


class RequestContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = _current_request.set(request)
        try:
            return self.get_response(request)
        finally:
            _current_request.reset(token)
