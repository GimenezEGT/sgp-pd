from django.urls import path

from . import views

app_name = "subdocuments"

urlpatterns = [
    path(
        "projetos/<int:project_id>/subdocumentos/",
        views.project_subdocuments,
        name="project_list",
    ),
    path("projetos/<int:project_id>/subdocumentos/novo/", views.subdocument_new, name="new"),
    path(
        "projetos/<int:project_id>/subdocumentos/autorizar/",
        views.flow_authorize,
        name="authorize",
    ),
    path("subdocumentos/<int:pk>/", views.subdocument_detail, name="detail"),
    path("subdocumentos/<int:pk>/editar/", views.subdocument_edit, name="edit"),
    path("subdocumentos/<int:pk>/linha/", views.table_row, name="row"),
    path("subdocumentos/<int:pk>/atualizar-derivados/", views.refresh, name="refresh"),
    path("subdocumentos/<int:pk>/migrar/", views.migrate, name="migrate"),
    path("subdocumentos/<int:pk>/aprovar/", views.approve, name="approve"),
]
