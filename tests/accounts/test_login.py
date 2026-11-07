"""Login pela rede (história 1): FR-001, FR-002, FR-004, FR-008, FR-027."""

import json

import pytest
from django.forms.models import model_to_dict
from django.urls import reverse

from sgp.accounts.models import LoginAttempt, User
from sgp.accounts.profiles import Profile
from sgp.accounts.services import GENERIC_LOGIN_ERROR, UNAVAILABLE_ERROR
from sgp.audit.models import AuditEvent

pytestmark = pytest.mark.django_db
PASSWORD = "Senha#Teste1"


def post_login(client, username, password=PASSWORD, **extra):
    return client.post(
        reverse("accounts:login"), {"username": username, "password": password, **extra}
    )


@pytest.mark.req("001:FR-001")
def test_login_aceito_sem_guardar_senha(client, directory, make_user, events):
    make_user("ana.silva", Profile.ANALYST)
    directory.add_person("ana.silva")
    response = post_login(client, "Ana.Silva")
    assert response.status_code == 302 and response["Location"] == reverse("core:home")
    user = User.objects.get(username="ana.silva")
    assert not user.has_usable_password()
    assert events("auth.login_succeeded")[0].actor == user
    attempt = LoginAttempt.objects.get(username="ana.silva")
    assert attempt.result == LoginAttempt.Result.SUCCESS


@pytest.mark.req("001:FR-002")
def test_primeiro_login_cria_cadastro_com_dados_da_rede(client, directory, events):
    directory.add_person(
        "novo.colab", full_name="Novo Colaborador", job_title="Técnico", email="novo@teste.local"
    )
    post_login(client, "novo.colab")
    user = User.objects.get(username="novo.colab")
    assert (user.full_name, user.job_title, user.email) == (
        "Novo Colaborador",
        "Técnico",
        "novo@teste.local",
    )
    created = events("accounts.user_created")[0]
    assert created.new_value["job_title"] == "Técnico"
    assert created.actor_username == "sistema"


@pytest.mark.req("001:FR-002")
def test_login_atualiza_dados_alterados_na_rede(client, directory, make_user, events):
    same = {
        "email": "ana@teste.local",
        "full_name": "Ana",
        "first_name": "Ana",
        "last_name": "Silva",
    }
    make_user("ana", Profile.ANALYST, job_title="Analista Júnior", **same)
    directory.add_person("ana", job_title="Analista Pleno", **same)
    post_login(client, "ana")
    updated = events("accounts.user_updated")
    assert len(updated) == 1
    assert updated[0].old_value == {"job_title": "Analista Júnior"}
    assert updated[0].new_value == {"job_title": "Analista Pleno"}


@pytest.mark.req("001:FR-002")
def test_login_sem_mudanca_nao_gera_alteracao(client, directory, make_user, events):
    make_user(
        "ana",
        Profile.ANALYST,
        job_title="Analista",
        email="ana@teste.local",
        full_name="Ana",
        first_name="Ana",
        last_name="Silva",
    )
    directory.add_person(
        "ana",
        job_title="Analista",
        email="ana@teste.local",
        full_name="Ana",
        first_name="Ana",
        last_name="Silva",
    )
    post_login(client, "ana")
    assert events("accounts.user_updated") == []


@pytest.mark.req("001:FR-004")
@pytest.mark.parametrize(
    "setup",
    ["senha_errada", "inexistente", "desativado_na_rede", "desativado_no_sistema"],
)
def test_recusas_tem_a_mesma_mensagem_generica(client, directory, make_user, events, setup):
    username = "pessoa.x"
    password = PASSWORD
    if setup == "senha_errada":
        directory.add_person(username)
        password = "errada"
    elif setup == "desativado_na_rede":
        directory.add_person(username, disabled=True)
    elif setup == "desativado_no_sistema":
        make_user(username, Profile.ANALYST, is_active=False)
        directory.add_person(username)
    response = post_login(client, username, password)
    assert response.status_code == 200
    assert GENERIC_LOGIN_ERROR in response.content.decode()
    assert "_auth_user_id" not in client.session
    failed = events("auth.login_failed")
    assert len(failed) == 1 and failed[0].object_id == username
    assert failed[0].actor is None and failed[0].actor_username == "anônimo"
    assert LoginAttempt.objects.get(username=username).result == LoginAttempt.Result.FAILURE


@pytest.mark.req("001:FR-004")
def test_servico_indisponivel_tem_mensagem_propria_e_nao_conta_falha(client, directory, events):
    directory.add_person("ana")
    directory.STATE["unavailable"] = True
    response = post_login(client, "ana")
    assert UNAVAILABLE_ERROR in response.content.decode()
    assert LoginAttempt.objects.get().result == LoginAttempt.Result.UNAVAILABLE
    assert len(events("auth.auth_unavailable")) == 1
    assert events("auth.login_failed") == []


@pytest.mark.req("001:FR-027")
def test_senha_nunca_aparece_em_eventos_ou_tentativas(client, directory, make_user):
    secret = "Segredo#Unico987"
    make_user("ana", Profile.ANALYST)
    directory.add_person("ana", password=secret)
    post_login(client, "ana", "Errada#Unica654")
    post_login(client, "ana", secret)
    dump = json.dumps(
        [model_to_dict(event) for event in AuditEvent.objects.all()]
        + [model_to_dict(attempt) for attempt in LoginAttempt.objects.all()],
        default=str,
    )
    assert secret not in dump and "Errada#Unica654" not in dump


@pytest.mark.req("001:FR-008")
def test_logout_encerra_sessao_e_registra(client, login_as, events):
    user = login_as(Profile.READER)
    response = client.post(reverse("accounts:logout"))
    assert response["Location"] == reverse("accounts:login")
    assert events("auth.logout")[0].actor == user
    assert client.get(reverse("core:home")).status_code == 302


def test_logout_exige_post(client, login_as):
    login_as(Profile.READER)
    assert client.get(reverse("accounts:logout")).status_code == 405


def test_login_respeita_next_seguro(client, directory, make_user):
    make_user("qa", Profile.QUALITY)
    directory.add_person("qa")
    response = post_login(client, "qa", next=reverse("audit:trail"))
    assert response["Location"] == reverse("audit:trail")
    client.logout()
    response = post_login(client, "qa", next="https://externo.exemplo/roubo")
    assert response["Location"] == reverse("core:home")


def test_pagina_de_login_e_formulario_invalido(client):
    assert client.get(reverse("accounts:login")).status_code == 200
    response = client.post(reverse("accounts:login"), {"username": "", "password": ""})
    assert response.status_code == 200
    assert not LoginAttempt.objects.exists()


def test_usuario_autenticado_que_abre_login_vai_para_o_inicio(client, login_as):
    login_as(Profile.READER)
    response = client.get(reverse("accounts:login"))
    assert response["Location"] == reverse("core:home")
