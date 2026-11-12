from django.urls import path

from . import views

app_name = "fulldoc"

urlpatterns = [
    path(
        "projetos/<int:project_id>/documento-completo/",
        views.project_document,
        name="project",
    ),
    path(
        "documentos-completos/pedidos/<int:pk>/",
        views.request_status,
        name="request_status",
    ),
    path("documentos-completos/<int:pk>/baixar/", views.download, name="download"),
]
