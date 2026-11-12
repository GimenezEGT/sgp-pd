"""Rotas do SGP-P&D. Não há admin do Django: toda alteração passa por telas que auditam."""

from django.urls import include, path

urlpatterns = [
    path("", include("sgp.core.urls")),
    path("", include("sgp.accounts.urls")),
    path("auditoria/", include("sgp.audit.urls")),
    path("projetos/", include("sgp.projects.urls")),
    path("cadastros/", include("sgp.catalog.urls")),
    path("arquivos/", include("sgp.files.urls")),
    path("listas/", include("sgp.vocab.urls")),
    path("modelos/", include("sgp.formtemplates.urls")),
    path("", include("sgp.subdocuments.urls")),
    path("assinaturas/", include("sgp.signatures.urls")),
    path("documentos/", include("sgp.documents.urls")),
    path("modelos-layout/", include("sgp.documents.layout_urls")),
    path("revisoes-modelos/", include("sgp.revisions.urls")),
    path("", include("sgp.studies.urls")),
    path("", include("sgp.notebook.urls")),
]
