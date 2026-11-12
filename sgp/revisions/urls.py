from django.urls import path

from . import views

app_name = "revisions"

urlpatterns = [
    path("", views.revision_list, name="list"),
    path("retirada/<int:pk>/pedir/", views.retirement_request, name="retirement_request"),
    path("retirada/<int:pk>/aprovar/", views.retirement_approve, name="retirement_approve"),
    path("retirada/<int:pk>/devolver/", views.retirement_return, name="retirement_return"),
    path("<str:kind>/<int:pk>/enviar/", views.submit, name="submit"),
    path("<str:kind>/<int:pk>/devolver/", views.return_revision, name="return"),
    path("<str:kind>/<int:pk>/aprovar/", views.approve, name="approve"),
    path("<str:kind>/<int:pk>/descartar/", views.discard, name="discard"),
    path("<str:kind>/<int:pk>/verificar/", views.verify, name="verify"),
    path("<str:kind>/<int:pk>/historico/", views.history, name="history"),
    path("<str:kind>/<int:pk>/comparar/", views.compare, name="compare"),
]
