from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("painel/", views.portfolio_view, name="portfolio"),
    path("painel/exportar/", views.export_view, name="export"),
    path("projetos/<int:project_id>/linha-do-tempo/", views.timeline_view, name="timeline"),
    path("pendencias/", views.pending_view, name="pending"),
]
