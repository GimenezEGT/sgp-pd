from django.urls import path

from . import views

app_name = "signatures"

urlpatterns = [
    path("fila/", views.queue_view, name="queue"),
    path("delegacoes/", views.delegations_view, name="delegations"),
    path("delegacoes/<int:pk>/encerrar/", views.delegation_end_view, name="delegation_end"),
    path("<str:kind>/<int:pk>/enviar/", views.submit_view, name="submit"),
    path("<str:kind>/<int:pk>/aprovar/", views.approve_view, name="approve"),
    path("<str:kind>/<int:pk>/devolver/", views.return_view, name="return"),
    path("<str:kind>/<int:pk>/revisar/", views.review_view, name="review"),
    path("<str:kind>/<int:pk>/nova-versao/", views.new_version_view, name="new_version"),
    path("<str:kind>/<int:pk>/verificar/", views.verify_view, name="verify"),
    path("<str:kind>/<int:pk>/versoes/<int:version>/", views.version_view, name="version"),
]
