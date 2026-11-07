"""Rotina diária de verificação, sem ação humana (FR-021)."""

import pytest
from django.conf import settings

from sgp.audit.models import ChainVerification
from sgp.audit.services import record_event
from sgp.audit.tasks import verify_chain_manual, verify_chain_scheduled

pytestmark = pytest.mark.req("001:FR-021")


def test_agendamento_diario_configurado():
    entry = settings.CELERY_BEAT_SCHEDULE["verificacao-diaria-da-trilha"]
    assert entry["task"] == "sgp.audit.verify_chain_scheduled"
    schedule = entry["schedule"]
    assert schedule.hour == {settings.AUDIT_VERIFY_HOUR}
    assert schedule.minute == {settings.AUDIT_VERIFY_MINUTE}
    assert settings.CELERY_TIMEZONE == "America/Sao_Paulo"


@pytest.mark.django_db
def test_tarefa_agendada_registra_verificacao():
    record_event("audit.exported", actor=None)
    assert verify_chain_scheduled.delay().get() == "intact"
    verification = ChainVerification.objects.get()
    assert verification.trigger == ChainVerification.Trigger.SCHEDULED
    assert verification.triggered_by is None


@pytest.mark.django_db
def test_tarefa_manual_registra_quem_pediu(make_user):
    user = make_user("pediu")
    assert verify_chain_manual.delay(user.pk).get() == "intact"
    assert ChainVerification.objects.get().triggered_by == user
