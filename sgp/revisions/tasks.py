"""Tarefa diária: entrada em vigência das versões de modelo com data futura (research R5)."""

from celery import shared_task


@shared_task(name="sgp.revisions.record_due", ignore_result=True)
def record_due() -> int:
    from .services import record_due as run

    return run()
