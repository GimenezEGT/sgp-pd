from django.urls import path

from . import views

app_name = "integrations"

urlpatterns = [
    path("integracoes/", views.queue, name="queue"),
    path("integracoes/mensagens/<int:pk>/reprocessar/", views.reprocess, name="reprocess"),
    path("integracoes/exportar/", views.export, name="export"),
    path("integracoes/mapeamento/", views.mapping_view, name="mapping"),
    path("integracoes/produto/", views.product, name="product"),
]
