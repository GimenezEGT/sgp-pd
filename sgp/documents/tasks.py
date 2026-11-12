"""Tarefa Celery da geração de documentos (research R7)."""

from celery import shared_task
from django.conf import settings


@shared_task(
    name="sgp.documents.generate",
    soft_time_limit=settings.DOCUMENT_GENERATION_TIME_LIMIT,
    ignore_result=True,
)
def generate(request_id: int) -> None:
    from .services import run_request

    run_request(request_id)
