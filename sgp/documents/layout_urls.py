from django.urls import path

from . import views

app_name = "layouts"

urlpatterns = [
    path("", views.layout_list, name="list"),
    path("<int:pk>/", views.layout_detail, name="detail"),
    path("<int:pk>/nova-versao/", views.layout_new_version, name="new_version"),
    path("<int:pk>/editar/", views.layout_edit, name="edit"),
    path("<int:pk>/previa/", views.layout_preview, name="preview"),
    path("<int:pk>/logotipo/", views.layout_logo, name="logo"),
]
