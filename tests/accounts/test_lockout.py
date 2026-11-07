"""Bloqueio de login por tentativas inválidas e desbloqueio (FR-006, FR-007, SC-006)."""

from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from sgp.accounts.models import LoginAttempt, LoginLockout
from sgp.accounts.profiles import Profile
from sgp.accounts.services import GENERIC_LOGIN_ERROR, release_lockout
from sgp.audit.models import AuditEvent

pytestmark = [pytest.mark.django_db, pytest.mark.req("001:FR-006"), pytest.mark.req("001:SC-006")]
GOOD = "Senha#Teste1"


def attempt(client, username, password):
    return client.post(reverse("accounts:login"), {"username": username, "password": password})


def fail(client, username, times):
    for _ in range(times):
        attempt(client, username, "errada")


def test_quinta_falha_bloqueia_e_senha_certa_e_recusada_sem_ir_a_rede(client, directory, make_user):
    make_user("ana", Profile.READER)
    directory.add_person("ana")
    fail(client, "ana", 5)
    lockout = LoginLockout.objects.get(username="ana")
    assert lockout.failure_count == 5 and lockout.is_active
    calls_before = directory.STATE["calls"]
    response = attempt(client, "ana", GOOD)
    assert "Login bloqueado" in response.content.decode()
    assert directory.STATE["calls"] == calls_before
    assert (
        LoginAttempt.objects.filter(username="ana", result=LoginAttempt.Result.BLOCKED).count() == 1
    )
    assert AuditEvent.objects.filter(event_type="auth.lockout_started").count() == 1
    assert AuditEvent.objects.filter(event_type="auth.login_blocked").count() == 1


def test_quatro_falhas_nao_bloqueiam(client, directory, make_user):
    make_user("ana", Profile.READER)
    directory.add_person("ana")
    fail(client, "ana", 4)
    assert not LoginLockout.objects.exists()
    assert attempt(client, "ana", GOOD)["Location"] == reverse("core:home")


def test_login_aceito_zera_a_contagem(client, directory, make_user):
    make_user("ana", Profile.READER)
    directory.add_person("ana")
    fail(client, "ana", 4)
    attempt(client, "ana", GOOD)
    client.logout()
    fail(client, "ana", 4)
    assert not LoginLockout.objects.exists()


def test_fim_do_bloqueio_libera_o_login(client, directory, make_user):
    make_user("ana", Profile.READER)
    directory.add_person("ana")
    fail(client, "ana", 5)
    LoginLockout.objects.filter(username="ana").update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    assert attempt(client, "ana", GOOD)["Location"] == reverse("core:home")


def test_contagem_recomeca_depois_do_bloqueio(client, directory, make_user):
    make_user("ana", Profile.READER)
    directory.add_person("ana")
    fail(client, "ana", 5)
    LoginLockout.objects.filter(username="ana").update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    fail(client, "ana", 4)
    assert LoginLockout.objects.filter(username="ana").count() == 1
    fail(client, "ana", 1)
    assert LoginLockout.objects.filter(username="ana").count() == 2


def test_indisponibilidade_nao_conta_como_falha(client, directory):
    directory.add_person("ana")
    directory.STATE["unavailable"] = True
    for _ in range(6):
        attempt(client, "ana", GOOD)
    assert not LoginLockout.objects.exists()


def test_usuario_inexistente_e_bloqueado_com_a_mesma_mensagem(client):
    for _ in range(5):
        response = attempt(client, "nao.existe", "qualquer")
        assert GENERIC_LOGIN_ERROR in response.content.decode()
    assert LoginLockout.objects.filter(username="nao.existe").exists()


@override_settings(LOGIN_MAX_FAILURES=2, LOGIN_LOCKOUT_MINUTES=60)
def test_parametros_configuraveis(client, directory):
    directory.add_person("ana")
    fail(client, "ana", 2)
    lockout = LoginLockout.objects.get(username="ana")
    assert lockout.failure_count == 2
    assert timedelta(minutes=59) < lockout.expires_at - lockout.started_at <= timedelta(minutes=60)


@pytest.mark.req("001:FR-007")
def test_administrador_desbloqueia_com_motivo(client, directory, make_user, login_as):
    directory.add_person("ana")
    make_user("ana", Profile.READER)
    fail(client, "ana", 5)
    lockout = LoginLockout.objects.get(username="ana")
    admin = login_as(Profile.ADMIN)
    page = client.get(reverse("accounts:lockouts")).content.decode()
    assert "ana" in page
    client.post(
        reverse("accounts:release_lockout", args=[lockout.pk]),
        {"reason": "Usuária confirmou identidade"},
    )
    lockout.refresh_from_db()
    assert lockout.released_by == admin and not lockout.is_active
    event = AuditEvent.objects.get(event_type="auth.lockout_released")
    assert event.reason == "Usuária confirmou identidade"
    client.logout()
    assert attempt(client, "ana", GOOD)["Location"] == reverse("core:home")


@pytest.mark.req("001:FR-007")
def test_desbloqueio_exige_motivo_e_bloqueio_ativo(make_user):
    admin = make_user("admin", Profile.ADMIN)
    lockout = LoginLockout.objects.create(
        username="ana", expires_at=timezone.now() + timedelta(minutes=10), failure_count=5
    )
    with pytest.raises(ValidationError):
        release_lockout(lockout, admin, "")
    release_lockout(lockout, admin, "ok")
    with pytest.raises(ValidationError, match="não está mais ativo"):
        release_lockout(lockout, admin, "de novo")


@pytest.mark.req("001:FR-007")
def test_somente_administrador_ve_bloqueios(client, login_as):
    login_as(Profile.QUALITY)
    assert client.get(reverse("accounts:lockouts")).status_code == 403
