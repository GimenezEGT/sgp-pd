from django.urls import path

from . import views

app_name = "documents"

urlpatterns = [
    path("verificar/", views.verify, name="verify"),
    path("pedidos/<int:pk>/", views.request_status, name="request"),
    path("arquivos/<int:pk>/baixar/", views.download, name="download"),
    path(
        "<str:kind>/<int:pk>/",
        views.document_history,
        name="history",
    ),
    path("<str:kind>/<int:pk>/gerar/", views.generate, name="generate"),
]
