from django.urls import path

from . import views, views_admin

app_name = "accounts"

urlpatterns = [
    path("entrar/", views.login_view, name="login"),
    path("sair/", views.logout_view, name="logout"),
    path("solicitar-acesso/", views.access_request_view, name="access_request"),
    path("administracao/pessoas/", views_admin.people_list, name="people"),
    path("administracao/pessoas/<int:user_id>/", views_admin.person_detail, name="person_detail"),
    path(
        "administracao/pessoas/<int:user_id>/perfis/conceder/",
        views_admin.grant_profile_view,
        name="grant_profile",
    ),
    path(
        "administracao/pessoas/<int:user_id>/perfis/<int:assignment_id>/revogar/",
        views_admin.revoke_profile_view,
        name="revoke_profile",
    ),
    path("administracao/solicitacoes/", views_admin.access_requests_list, name="access_requests"),
    path(
        "administracao/solicitacoes/<int:request_id>/decidir/",
        views_admin.decide_access_request_view,
        name="decide_access_request",
    ),
    path("administracao/bloqueios/", views_admin.lockouts_list, name="lockouts"),
    path(
        "administracao/bloqueios/<int:lockout_id>/desbloquear/",
        views_admin.release_lockout_view,
        name="release_lockout",
    ),
]
