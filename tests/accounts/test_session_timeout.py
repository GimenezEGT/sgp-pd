"""Encerramento de sessão por inatividade (FR-005, SC-006)."""

import pytest
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from sgp.accounts.profiles import Profile
from sgp.audit.models import AuditEvent
from sgp.core.middleware import EXPIRED_MESSAGE, LAST_ACTIVITY_KEY

pytestmark = [pytest.mark.django_db, pytest.mark.req("001:FR-005"), pytest.mark.req("001:SC-006")]


def set_last_activity(client, minutes_ago):
    session = client.session
    session[LAST_ACTIVITY_KEY] = timezone.now().timestamp() - minutes_ago * 60
    session.save()


def test_sessao_parada_alem_do_limite_e_encerrada(client, login_as):
    user = login_as(Profile.READER)
    assert client.get(reverse("core:home")).status_code == 200
    set_last_activity(client, 31)
    response = client.get(reverse("core:home"))
    assert response.status_code == 302
    assert response["Location"].startswith(reverse("accounts:login"))
    assert "_auth_user_id" not in client.session
    event = AuditEvent.objects.get(event_type="auth.session_expired")
    assert event.actor == user and "ultimo_acesso" in event.old_value
    page = client.get(response["Location"])
    assert EXPIRED_MESSAGE in page.content.decode()


def test_atividade_dentro_do_limite_renova_a_sessao(client, login_as):
    login_as(Profile.READER)
    client.get(reverse("core:home"))
    set_last_activity(client, 29)
    assert client.get(reverse("core:home")).status_code == 200
    assert timezone.now().timestamp() - client.session[LAST_ACTIVITY_KEY] < 60
    assert not AuditEvent.objects.filter(event_type="auth.session_expired").exists()


@override_settings(SESSION_IDLE_TIMEOUT_MINUTES=5)
def test_limite_e_configuravel(client, login_as):
    login_as(Profile.READER)
    client.get(reverse("core:home"))
    set_last_activity(client, 6)
    assert client.get(reverse("core:home")).status_code == 302
