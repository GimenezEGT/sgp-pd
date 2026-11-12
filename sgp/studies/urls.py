from django.urls import path

from . import views

app_name = "studies"

urlpatterns = [
    path("projetos/<int:project_id>/estudos/", views.project_studies, name="project_list"),
    path("estudos/<int:pk>/", views.study_detail, name="detail"),
    path("estudos/<int:pk>/editar/", views.study_edit, name="edit"),
    path("estudos/<int:pk>/nao-aplicavel/", views.study_not_applicable, name="not_applicable"),
    path("estudos/<int:pk>/importar/", views.study_import, name="import"),
    path("estudos/<int:pk>/nova-versao/", views.study_new_version, name="new_version"),
]
