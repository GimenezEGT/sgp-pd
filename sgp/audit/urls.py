from django.urls import path

from . import views

app_name = "audit"

urlpatterns = [
    path("", views.trail, name="trail"),
    path("exportar/", views.export, name="export"),
    path("integridade/", views.integrity, name="integrity"),
    path("integridade/verificar/", views.verify_now, name="verify_now"),
]
