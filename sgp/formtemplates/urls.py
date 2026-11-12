from django.urls import path

from . import views

app_name = "formtemplates"

urlpatterns = [
    path("", views.template_list, name="list"),
    path("<int:pk>/", views.template_detail, name="detail"),
    path("<int:pk>/nova-versao/", views.template_new_version, name="new_version"),
    path("<int:pk>/editar/", views.template_edit, name="edit"),
]
