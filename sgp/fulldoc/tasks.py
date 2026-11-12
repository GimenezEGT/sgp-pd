"""Tarefa Celery do documento completo (research R3)."""

from celery import shared_task
from django.conf import settings


@shared_task(
    name="sgp.fulldoc.generate",
    soft_time_limit=max(settings.DOCUMENT_GENERATION_TIME_LIMIT, 600),
    ignore_result=True,
)
def generate(request_id: int) -> None:
    from .services import run_request

    run_request(request_id)
