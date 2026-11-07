"""Tarefas de fundo da trilha: verificação diária (agendada) e sob demanda."""

from celery import shared_task
from django.contrib.auth import get_user_model

from .models import ChainVerification
from .services import verify_chain


@shared_task(name="sgp.audit.verify_chain_scheduled")
def verify_chain_scheduled() -> str:
    return verify_chain(trigger=ChainVerification.Trigger.SCHEDULED).status


@shared_task(name="sgp.audit.verify_chain_manual")
def verify_chain_manual(user_id: int) -> str:
    user = get_user_model().objects.filter(pk=user_id).first()
    return verify_chain(trigger=ChainVerification.Trigger.MANUAL, triggered_by=user).status
