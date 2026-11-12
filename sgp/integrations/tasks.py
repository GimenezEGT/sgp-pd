"""Tarefas Celery da integração (research R4)."""

from celery import shared_task


@shared_task(name="sgp.integrations.dispatch", ignore_result=True)
def dispatch(message_id: int) -> None:
    from .services import dispatch as send

    send(message_id)


@shared_task(name="sgp.integrations.process_due", ignore_result=True)
def process_due() -> None:
    from .services import process_due as sweep

    sweep()
