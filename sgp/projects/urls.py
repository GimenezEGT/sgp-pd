from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.project_list, name="list"),
    path("novo/", views.project_new, name="new"),
    path("<int:project_id>/", views.project_detail, name="detail"),
    path("<int:project_id>/editar/", views.project_edit, name="edit"),
    path("<int:project_id>/tap/", views.charter_edit, name="charter"),
    path("<int:project_id>/plano-de-negocios/", views.business_plan_edit, name="business_plan"),
    path("<int:project_id>/equipe/incluir/", views.member_add, name="member_add"),
    path("<int:project_id>/equipe/<int:member_id>/encerrar/", views.member_end, name="member_end"),
    path("<int:project_id>/marcos/incluir/", views.milestone_add, name="milestone_add"),
    path(
        "<int:project_id>/marcos/<int:milestone_id>/",
        views.milestone_update,
        name="milestone_update",
    ),
    path(
        "<int:project_id>/marcos/<int:milestone_id>/cancelar/",
        views.milestone_cancel,
        name="milestone_cancel",
    ),
    path("<int:project_id>/submeter/", views.project_submit, name="submit"),
    path("<int:project_id>/aprovar/", views.project_approve, name="approve"),
    path("<int:project_id>/devolver/", views.project_return, name="return"),
]
