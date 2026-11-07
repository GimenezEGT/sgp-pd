"""Pessoa sem perfil e solicitação de acesso (FR-003, FR-015)."""

import pytest
from django.urls import reverse

from sgp.accounts.models import AccessRequest, ProfileAssignment
from sgp.accounts.profiles import Profile
from sgp.accounts.services import revoke_profile

pytestmark = [pytest.mark.django_db, pytest.mark.req("001:FR-003")]


def test_login_sem_perfil_vai_direto_para_solicitar_acesso(client, directory, events):
    directory.add_person("sem.perfil")
    response = client.post(
        reverse("accounts:login"), {"username": "sem.perfil", "password": "Senha#Teste1"}
    )
    assert response["Location"] == reverse("accounts:access_request")
    assert events("auth.permission_denied") == []


@pytest.mark.req("001:FR-015")
def test_sem_perfil_e_recusado_em_outras_paginas_e_registrado(client, login_as, events):
    user = login_as()
    for url in (reverse("core:home"), reverse("audit:trail"), reverse("accounts:people")):
        response = client.get(url)
        assert response.status_code == 302
        assert response["Location"] == reverse("accounts:access_request")
    denied = events("auth.permission_denied")
    assert len(denied) == 3
    assert all(event.actor == user for event in denied)
    assert denied[0].new_value["motivo"] == "pessoa sem perfil ativo"


def test_sem_perfil_ve_instrucoes_e_registra_solicitacao(client, login_as, events):
    user = login_as()
    page = client.get(reverse("accounts:access_request"))
    assert page.status_code == 200
    assert "ainda não tem perfil" in page.content.decode()
    response = client.post(
        reverse("accounts:access_request"),
        {"justification": "Preciso registrar experimentos do projeto de extração."},
        follow=True,
    )
    assert response.status_code == 200
    request = AccessRequest.objects.get(user=user)
    assert request.status == AccessRequest.Status.PENDING
    assert events("accounts.access_requested")[0].new_value["justificativa"].startswith("Preciso")
    assert "Preciso registrar experimentos" in response.content.decode()


def test_justificativa_obrigatoria(client, login_as):
    login_as()
    response = client.post(reverse("accounts:access_request"), {"justification": "   "})
    assert response.status_code == 200
    assert not AccessRequest.objects.exists()


def test_sem_perfil_pode_sair(client, login_as):
    login_as()
    assert client.post(reverse("accounts:logout")).status_code == 302


def test_pessoa_que_perde_o_ultimo_perfil_passa_a_ser_recusada(client, login_as, make_user):
    admin = make_user("admin", Profile.ADMIN)
    user = login_as(Profile.READER)
    assert client.get(reverse("core:home")).status_code == 200
    revoke_profile(ProfileAssignment.objects.get(user=user), by=admin, reason="Saiu do projeto")
    response = client.get(reverse("core:home"))
    assert response["Location"] == reverse("accounts:access_request")


def test_pessoa_desativada_com_sessao_aberta_e_desconectada(client, login_as):
    user = login_as(Profile.READER)
    user.is_active = False
    user.save()
    response = client.get(reverse("core:home"))
    assert response.status_code == 302
    assert "_auth_user_id" not in client.session
