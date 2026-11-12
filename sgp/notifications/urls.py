from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("notificacoes/preferencias/", views.preferences, name="preferences"),
]
