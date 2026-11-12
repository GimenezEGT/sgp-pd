from django.urls import path

from . import views

app_name = "notebook"

urlpatterns = [
    path("caderno/", views.search_view, name="search"),
    path("projetos/<int:project_id>/caderno/", views.project_notebook, name="project"),
    path("projetos/<int:project_id>/caderno/nova/", views.entry_create, name="create"),
    path("caderno/entradas/<int:pk>/", views.entry_detail, name="detail"),
    path("caderno/entradas/<int:pk>/editar/", views.entry_edit, name="edit"),
    path("caderno/entradas/<int:pk>/materiais/", views.material_add, name="material_add"),
    path("caderno/materiais/<int:pk>/retirar/", views.material_remove, name="material_remove"),
    path("caderno/entradas/<int:pk>/anexos/", views.attachment_add, name="attachment_add"),
    path("caderno/anexos/<int:pk>/retirar/", views.attachment_remove, name="attachment_remove"),
    path("caderno/entradas/<int:pk>/relevancia/", views.relevance, name="relevance"),
    path("caderno/entradas/<int:pk>/assinar/", views.sign, name="sign"),
    path("caderno/entradas/<int:pk>/testemunhar/", views.witness, name="witness"),
    path("caderno/entradas/<int:pk>/adendos/", views.addendum_add, name="addendum_add"),
    path("caderno/entradas/<int:pk>/vinculos/", views.link_add, name="link_add"),
    path("caderno/vinculos/<int:pk>/retirar/", views.link_remove, name="link_remove"),
    path("caderno/entradas/<int:pk>/promover/", views.promote, name="promote"),
    path("caderno/modelos/", views.template_list, name="templates"),
    path("caderno/modelos/<int:pk>/", views.template_detail, name="template_detail"),
    path(
        "caderno/modelos/<int:pk>/desativar/",
        views.template_deactivate,
        name="template_deactivate",
    ),
]
