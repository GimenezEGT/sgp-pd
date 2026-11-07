from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.index, name="index"),
    path("insumos/importar/", views.import_upload, name="import"),
    path("insumos/importar/<int:pk>/", views.import_batch, name="import_batch"),
    path(
        "insumos/importar/<int:pk>/rejeicoes.csv",
        views.import_rejections,
        name="import_rejections",
    ),
    path("insumos/modelo.csv", views.import_template, name="import_template"),
    path("<str:kind>/", views.record_list, name="list"),
    path("<str:kind>/buscar/", views.search, name="search"),
    path("<str:kind>/novo/", views.record_new, name="new"),
    path("<str:kind>/<int:pk>/", views.record_detail, name="detail"),
    path("<str:kind>/<int:pk>/editar/", views.record_edit, name="edit"),
    path("<str:kind>/<int:pk>/situacao/", views.record_status, name="status"),
]
