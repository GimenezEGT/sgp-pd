"""Rotas do SGP-P&D. Não há admin do Django: toda alteração passa por telas que auditam."""

from django.urls import include, path

urlpatterns = [
    path("", include("sgp.core.urls")),
    path("", include("sgp.accounts.urls")),
    path("auditoria/", include("sgp.audit.urls")),
]
