from django.urls import path

from . import views

app_name = "operations"

urlpatterns = [
    path("operacao/", views.panel, name="panel"),
    path("operacao/copias/executar/", views.backup_now, name="backup_now"),
    path("operacao/restauracao/executar/", views.restore_now, name="restore_now"),
    path(
        "operacao/qualificacao/instalacao/",
        views.qualify_installation,
        name="qualify_installation",
    ),
    path("operacao/qualificacao/operacao/", views.qualify_operation, name="qualify_operation"),
    path("operacao/qualificacao/<int:pk>/relatorio/", views.report, name="report"),
    path("operacao/revisao-de-acessos/", views.access_review_export, name="access_review"),
]
