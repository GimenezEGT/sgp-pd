"""Varredura de todas as rotas: ninguém sem permissão abre função alguma (SC-002, FR-003, FR-015).

Toda rota nova precisa entrar em ROUTE_CONTRACT com o método e os perfis exigidos; o teste falha
se aparecer rota sem contrato, o que obriga a documentar a permissão de cada tela.
"""

import pytest
from django.urls import URLPattern, URLResolver, get_resolver, reverse

from sgp.accounts.profiles import AUDIT_TRAIL_PROFILES, INTEGRITY_PROFILES, Profile
from sgp.catalog.permissions import EDITOR_PROFILES

ANONYMOUS = "anonymous"
AUTHENTICATED = "authenticated"
ANY_PROFILE = "any_profile"
# Acesso decidido pelo projeto (membro/líder/perfil global); coberto em tests/projects.
PROJECT_ACCESS = "project_access"

ROUTE_CONTRACT = {
    "accounts:login": ("GET", ANONYMOUS),
    "core:health": ("GET", ANONYMOUS),
    "accounts:logout": ("POST", AUTHENTICATED),
    "accounts:access_request": ("GET", AUTHENTICATED),
    "core:home": ("GET", ANY_PROFILE),
    "accounts:people": ("GET", {Profile.ADMIN}),
    "accounts:person_detail": ("GET", {Profile.ADMIN}),
    "accounts:grant_profile": ("POST", {Profile.ADMIN}),
    "accounts:revoke_profile": ("POST", {Profile.ADMIN}),
    "accounts:deactivate_person": ("POST", {Profile.ADMIN}),
    "accounts:reactivate_person": ("POST", {Profile.ADMIN}),
    "accounts:access_requests": ("GET", {Profile.ADMIN}),
    "accounts:decide_access_request": ("POST", {Profile.ADMIN}),
    "accounts:lockouts": ("GET", {Profile.ADMIN}),
    "accounts:release_lockout": ("POST", {Profile.ADMIN}),
    "audit:trail": ("GET", AUDIT_TRAIL_PROFILES),
    "audit:export": ("GET", AUDIT_TRAIL_PROFILES),
    "audit:integrity": ("GET", INTEGRITY_PROFILES),
    "audit:verify_now": ("POST", INTEGRITY_PROFILES),
    "projects:list": ("GET", ANY_PROFILE),
    "projects:new": ("GET", {Profile.PROJECT_LEADER, Profile.RD_MANAGER}),
    "projects:detail": ("GET", PROJECT_ACCESS),
    "projects:edit": ("GET", PROJECT_ACCESS),
    "projects:charter": ("GET", PROJECT_ACCESS),
    "projects:business_plan": ("GET", PROJECT_ACCESS),
    "projects:member_add": ("POST", PROJECT_ACCESS),
    "projects:member_end": ("POST", PROJECT_ACCESS),
    "projects:milestone_add": ("POST", PROJECT_ACCESS),
    "projects:milestone_update": ("POST", PROJECT_ACCESS),
    "projects:milestone_cancel": ("POST", PROJECT_ACCESS),
    "projects:submit": ("POST", PROJECT_ACCESS),
    "projects:approve": ("POST", {Profile.RD_MANAGER}),
    "projects:return": ("POST", {Profile.RD_MANAGER}),
    # Feature 003: consulta por qualquer perfil (lotes: acesso ao projeto, coberto em
    # tests/catalog); edição só pelos editores dos cadastros.
    "catalog:index": ("GET", ANY_PROFILE),
    "catalog:list": ("GET", ANY_PROFILE),
    "catalog:search": ("GET", ANY_PROFILE),
    "catalog:detail": ("GET", ANY_PROFILE),
    "catalog:new": ("GET", EDITOR_PROFILES),
    "catalog:edit": ("GET", EDITOR_PROFILES),
    "catalog:status": ("POST", EDITOR_PROFILES),
    "catalog:import": ("GET", EDITOR_PROFILES),
    "catalog:import_batch": ("GET", EDITOR_PROFILES),
    "catalog:import_rejections": ("GET", EDITOR_PROFILES),
    "catalog:import_template": ("GET", EDITOR_PROFILES),
    # Arquivo: decidido pela política do registro dono (tests/files/test_download.py).
    "files:download": ("GET", ANY_PROFILE),
    "vocab:lists": ("GET", {Profile.QUALITY}),
    "vocab:detail": ("GET", {Profile.QUALITY}),
    "vocab:term": ("POST", {Profile.QUALITY}),
    # Feature 004
    "formtemplates:list": ("GET", ANY_PROFILE),
    "formtemplates:detail": ("GET", ANY_PROFILE),
    "formtemplates:new_version": ("POST", {Profile.QUALITY}),
    "formtemplates:edit": ("GET", {Profile.QUALITY}),
    "formtemplates:publish": ("POST", {Profile.QUALITY}),
    "subdocuments:project_list": ("GET", PROJECT_ACCESS),
    "subdocuments:new": ("POST", PROJECT_ACCESS),
    "subdocuments:authorize": ("POST", {Profile.RD_MANAGER}),
    "subdocuments:detail": ("GET", PROJECT_ACCESS),
    "subdocuments:edit": ("GET", PROJECT_ACCESS),
    "subdocuments:row": ("GET", PROJECT_ACCESS),
    "subdocuments:refresh": ("POST", PROJECT_ACCESS),
    "subdocuments:migrate": ("POST", {Profile.RD_MANAGER}),
    # Feature 005: o documento decide (acesso ao projeto, editor, Gestor ou delegado).
    "signatures:queue": ("GET", ANY_PROFILE),
    "signatures:delegations": ("GET", {Profile.RD_MANAGER}),
    "signatures:delegation_end": ("POST", {Profile.RD_MANAGER}),
    "signatures:submit": ("GET", PROJECT_ACCESS),
    "signatures:approve": ("GET", PROJECT_ACCESS),
    "signatures:return": ("POST", PROJECT_ACCESS),
    "signatures:review": ("POST", PROJECT_ACCESS),
    "signatures:new_version": ("POST", PROJECT_ACCESS),
    "signatures:verify": ("POST", PROJECT_ACCESS),
    "signatures:version": ("GET", PROJECT_ACCESS),
    # Feature 006: documentos gerados (acesso ao documento, coberto em tests/documents) e
    # modelos de layout (consulta por todos; edição, prévia e publicação pela Qualidade/AR).
    "documents:verify": ("GET", ANY_PROFILE),
    "documents:history": ("GET", PROJECT_ACCESS),
    "documents:generate": ("POST", PROJECT_ACCESS),
    "documents:request": ("GET", PROJECT_ACCESS),
    "documents:download": ("GET", PROJECT_ACCESS),
    "layouts:list": ("GET", ANY_PROFILE),
    "layouts:detail": ("GET", ANY_PROFILE),
    "layouts:logo": ("GET", ANY_PROFILE),
    "layouts:new_version": ("POST", {Profile.QUALITY}),
    "layouts:edit": ("GET", {Profile.QUALITY}),
    "layouts:preview": ("GET", {Profile.QUALITY}),
    "layouts:publish": ("POST", {Profile.QUALITY}),
}


def collect_routes(resolver=None, namespace=""):
    resolver = resolver or get_resolver()
    routes = []
    for entry in resolver.url_patterns:
        if isinstance(entry, URLResolver):
            child_ns = f"{namespace}{entry.namespace}:" if entry.namespace else namespace
            routes.extend(collect_routes(entry, child_ns))
        elif isinstance(entry, URLPattern) and entry.name:
            routes.append((f"{namespace}{entry.name}", list(entry.pattern.converters)))
    return routes


ROUTES = collect_routes()


def url_for(name, params):
    return reverse(name, kwargs={param: 999999 for param in params})


def call(client, name, params):
    method, _ = ROUTE_CONTRACT[name]
    url = url_for(name, params)
    return client.post(url) if method == "POST" else client.get(url)


def test_toda_rota_tem_contrato_de_permissao():
    names = {name for name, _ in ROUTES}
    assert names == set(ROUTE_CONTRACT), f"Rotas sem contrato: {names - set(ROUTE_CONTRACT)}"


@pytest.mark.django_db
@pytest.mark.req("001:SC-002")
@pytest.mark.parametrize("name,params", ROUTES)
def test_anonimo_e_levado_ao_login(client, name, params):
    if ROUTE_CONTRACT[name][1] == ANONYMOUS:
        return
    response = call(client, name, params)
    assert response.status_code == 302
    assert response["Location"].startswith(reverse("accounts:login"))


@pytest.mark.django_db
@pytest.mark.req("001:SC-002")
@pytest.mark.req("001:FR-003")
@pytest.mark.parametrize("name,params", ROUTES)
def test_pessoa_sem_perfil_so_ve_solicitar_acesso(client, login_as, name, params):
    required = ROUTE_CONTRACT[name][1]
    if required in (ANONYMOUS, AUTHENTICATED):
        return
    login_as()
    response = call(client, name, params)
    assert response.status_code == 302
    assert response["Location"] == reverse("accounts:access_request")


@pytest.mark.django_db
@pytest.mark.req("001:SC-002")
@pytest.mark.req("001:FR-015")
@pytest.mark.parametrize("name,params", ROUTES)
def test_perfil_sem_permissao_recebe_403(client, login_as, name, params):
    required = ROUTE_CONTRACT[name][1]
    if not isinstance(required, set | frozenset):
        return
    others = [profile for profile in Profile if profile not in required]
    login_as(*others)
    assert call(client, name, params).status_code == 403
