from django.urls import path

from . import views

app_name = "dossier"

urlpatterns = [
    path("projetos/<int:project_id>/dossie/", views.project_dossier, name="project"),
    path(
        "projetos/<int:project_id>/dossie/complementos/<str:item_key>/",
        views.supplement,
        name="supplement",
    ),
    path("dossie/versoes/<int:pk>/arquivo/<str:kind>/", views.download, name="download"),
    path("dossie/versoes/<int:pk>/envio/", views.submit, name="submit"),
    path("dossie/versoes/<int:pk>/aditamento/", views.addendum, name="addendum"),
    path("dossie/envios/<int:pk>/resultado/", views.result, name="result"),
    path("dossie/textos/", views.texts, name="texts"),
    path("dossie/textos/<int:pk>/aprovar/", views.text_approve, name="text_approve"),
    path("dossie/definicao/", views.definition_view, name="definition"),
    path("dossie/empresa/", views.company_view, name="company"),
]
