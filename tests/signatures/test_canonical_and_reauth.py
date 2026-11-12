"""Conteúdo canônico e reautenticação com bloqueio (FR-006, FR-008, FR-010, SC-004 da feature 005)."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from sgp.signatures.canonical import canonical_json, content_hash
from sgp.signatures.models import SignatureAttempt, SignatureLock
from sgp.signatures.reauth import SignatureError, reauthenticate

pytestmark = [pytest.mark.django_db]


@pytest.mark.req("005:FR-010")
def test_json_canonico_estavel():
    first = {"b": [1, {"y": Decimal("1.50"), "x": date(2026, 11, 7)}], "a": "ação"}
    second = {"a": "ação", "b": [1, {"x": date(2026, 11, 7), "y": Decimal("1.50")}]}
    assert canonical_json(first) == canonical_json(second)
    assert canonical_json(first) == '{"a":"ação","b":[1,{"x":"2026-11-07","y":"1.50"}]}'
    assert content_hash(first) == content_hash(second) and len(content_hash(first)) == 64
    assert content_hash({"a": "ação"}) != content_hash({"a": "acao"})


@pytest.fixture
def person(make_user, directory):
    user = make_user("signatario")
    directory.add_person("signatario", password="Certa#123")
    return user


@pytest.mark.req("005:FR-006")
def test_senha_certa_registra_tentativa_sem_guardar_a_senha(person):
    reauthenticate(None, person, "Certa#123")
    attempt = SignatureAttempt.objects.get(user=person)
    assert attempt.success is True
    assert "Certa#123" not in str(attempt.__dict__)


@pytest.mark.req("005:FR-006")
def test_senha_errada_ou_vazia_e_recusada(person, events):
    with pytest.raises(SignatureError, match="Informe a sua senha"):
        reauthenticate(None, person, "")
    with pytest.raises(SignatureError, match="Senha de rede incorreta"):
        reauthenticate(None, person, "errada")
    assert events("signatures.failed")[-1].new_value == {"tentativas_seguidas": 1}


@pytest.mark.req("005:FR-008")
@pytest.mark.req("005:SC-004")
def test_terceira_falha_bloqueia_e_gera_alerta(person, events, settings):
    for _ in range(2):
        with pytest.raises(SignatureError, match="incorreta"):
            reauthenticate(None, person, "errada")
    with pytest.raises(SignatureError, match="terceira vez seguida"):
        reauthenticate(None, person, "errada")
    lock = SignatureLock.objects.get(user=person)
    assert lock.expires_at > timezone.now() + timedelta(minutes=settings.SIGNATURE_LOCK_MINUTES - 1)
    assert events("signatures.blocked")
    with pytest.raises(SignatureError, match="bloqueada até"):
        reauthenticate(None, person, "Certa#123")
    SignatureLock.objects.filter(pk=lock.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    reauthenticate(None, person, "Certa#123")


@pytest.mark.req("005:FR-008")
def test_acerto_zera_a_contagem(person):
    for _ in range(2):
        with pytest.raises(SignatureError):
            reauthenticate(None, person, "errada")
    reauthenticate(None, person, "Certa#123")
    with pytest.raises(SignatureError, match="Senha de rede incorreta"):
        reauthenticate(None, person, "errada")
    assert not SignatureLock.objects.filter(user=person).exists()


@pytest.mark.req("005:FR-008")
def test_diretorio_indisponivel_nao_conta_falha(person, directory):
    directory.STATE["unavailable"] = True
    for _ in range(4):
        with pytest.raises(SignatureError, match="indisponível"):
            reauthenticate(None, person, "Certa#123")
    assert not SignatureAttempt.objects.filter(user=person).exists()
    assert not SignatureLock.objects.filter(user=person).exists()
