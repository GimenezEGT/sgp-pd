"""Tarefas Celery da operação (research R6 da feature 014)."""

import logging

from celery import shared_task
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)


def _user(user_id):
    return get_user_model().objects.filter(pk=user_id).first() if user_id else None


@shared_task(name="sgp.operations.backup", ignore_result=True)
def backup(kind: str = "scheduled", user_id: int | None = None) -> None:
    from .backup import BackupBusy, run_backup

    try:
        run_backup(kind=kind, by=_user(user_id))
    except BackupBusy as exc:
        logger.info("Cópia não iniciada: %s", exc)


@shared_task(name="sgp.operations.restore_test", ignore_result=True)
def restore_test(kind: str = "scheduled", user_id: int | None = None) -> None:
    from .restore import RestoreBusy, run_restore_test

    try:
        run_restore_test(kind=kind, by=_user(user_id))
    except RestoreBusy as exc:
        logger.info("Teste de restauração não iniciado: %s", exc)


@shared_task(name="sgp.operations.check_freshness", ignore_result=True)
def check_freshness() -> None:
    from .restore import check_freshness as check

    check()


@shared_task(name="sgp.operations.qualification", ignore_result=True)
def qualification(kind: str, user_id: int) -> None:
    from .qualification import execute

    user = _user(user_id)
    if user is None:
        logger.warning("Qualificação %s sem executor %s", kind, user_id)
        return
    execute(kind, by=user)
