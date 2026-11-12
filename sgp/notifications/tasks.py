"""Tarefas Celery das notificações (research R8)."""

from celery import shared_task


@shared_task(name="sgp.notifications.send", ignore_result=True)
def send(notification_id: int) -> None:
    from .services import send as send_notification

    send_notification(notification_id)


@shared_task(name="sgp.notifications.daily_digest", ignore_result=True)
def daily_digest() -> None:
    from .services import daily_digest as run_digest

    run_digest()
