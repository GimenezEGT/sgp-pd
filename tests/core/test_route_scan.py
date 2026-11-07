"""Varredura de todas as rotas: ninguém sem permissão abre função alguma (SC-002, FR-003, FR-015).

Toda rota nova precisa entrar em ROUTE_CONTRACT com o método e os perfis exigidos; o teste falha
se aparecer rota sem contrato, o que obriga a documentar a permissão de cada tela.
"""

import pytest
from django.urls import URLPattern, URLResolver, get_resolver, reverse

from sgp.accounts.profiles import AUDIT_TRAIL_PROFILES, INTEGRITY_PROFILES, Profile

ANONYMOUS = "anonymous"
AUTHENTICATED = "authenticated"
ANY_PROFILE = "any_profile"

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
    "accounts:access_requests": ("GET", {Profile.ADMIN}),
    "accounts:decide_access_request": ("POST", {Profile.ADMIN}),
    "accounts:lockouts": ("GET", {Profile.ADMIN}),
    "accounts:release_lockout": ("POST", {Profile.ADMIN}),
    "audit:trail": ("GET", AUDIT_TRAIL_PROFILES),
    "audit:export": ("GET", AUDIT_TRAIL_PROFILES),
    "audit:integrity": ("GET", INTEGRITY_PROFILES),
    "audit:verify_now": ("POST", INTEGRITY_PROFILES),
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
