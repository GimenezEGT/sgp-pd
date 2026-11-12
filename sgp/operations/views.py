"""Painel de operação e validação (contrato rotas-ui.md da feature 014)."""

from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import content_disposition_header
from django.views.decorators.http import require_GET, require_POST

from sgp.accounts.profiles import Profile, active_profiles, deny_access
from sgp.audit.services import record_event
from sgp.files.storage import read_verified

from . import access_review, backup, qualification, restore, tasks
from .models import (
    BackupRun,
    BackupStatus,
    QualificationKind,
    QualificationRun,
    RestoreStatus,
    RestoreTest,
)

VIEWERS = {Profile.ADMIN, Profile.QUALITY}
IT_ONLY = "só a TI (Administrador do sistema) pede cópias, testes e a qualificação de instalação"
VIEW_ONLY = "só a TI e a Garantia da Qualidade acompanham a operação e a validação"


def _profiles(request):
    return active_profiles(request.user)


@require_GET
def panel(request):
    profiles = _profiles(request)
    if not VIEWERS & profiles:
        return deny_access(request, VIEW_ONLY)
    now = timezone.now()
    latest_backup = backup.latest_success()
    latest_test = restore.latest_test()
    context = {
        "backups": BackupRun.objects.select_related("requested_by")[:30],
        "tests": RestoreTest.objects.select_related("backup", "requested_by")[:12],
        "runs": QualificationRun.objects.select_related("executed_by", "report")[:20],
        "is_admin": Profile.ADMIN in profiles,
        "can_oq": bool({Profile.ADMIN, Profile.QUALITY} & profiles),
        "backup_stale": latest_backup is None
        or not latest_backup.finished_at
        or latest_backup.finished_at < now - timedelta(hours=settings.BACKUP_MAX_AGE_HOURS),
        "restore_overdue": latest_test is None
        or latest_test.status != RestoreStatus.PASSED
        or latest_test.started_at < now - timedelta(days=settings.RESTORE_TEST_MAX_AGE_DAYS),
        "latest_backup": latest_backup,
        "latest_test": latest_test,
        "running_backup": BackupRun.objects.filter(status=BackupStatus.RUNNING).exists(),
        "running_test": RestoreTest.objects.filter(status=RestoreStatus.RUNNING).exists(),
        "max_age_hours": settings.BACKUP_MAX_AGE_HOURS,
        "restore_max_days": settings.RESTORE_TEST_MAX_AGE_DAYS,
        "destination": settings.BACKUP_DIR,
        "keep_days": settings.BACKUP_KEEP_DAYS,
    }
    return render(request, "operations/panel.html", context)


def _enqueue(task, **kwargs):
    transaction.on_commit(lambda: task.delay(**kwargs))


@require_POST
def backup_now(request):
    if Profile.ADMIN not in _profiles(request):
        return deny_access(request, IT_ONLY)
    if backup.is_running():
        messages.error(request, "Já há uma cópia de segurança em andamento.")
        return redirect("operations:panel")
    record_event(
        "operations.backup_requested",
        actor=request.user,
        object_type="operations.backuprun",
        object_id="",
        object_repr="Cópia de segurança pedida",
        request=request,
    )
    _enqueue(tasks.backup, kind="manual", user_id=request.user.pk)
    messages.success(
        request, "Cópia de segurança pedida; o resultado aparece nesta página em alguns minutos."
    )
    return redirect("operations:panel")


@require_POST
def restore_now(request):
    if Profile.ADMIN not in _profiles(request):
        return deny_access(request, IT_ONLY)
    target = backup.latest_success()
    if target is None:
        messages.error(request, "Não há cópia de segurança bem-sucedida para testar.")
        return redirect("operations:panel")
    record_event(
        "operations.restore_requested",
        actor=request.user,
        obj=target,
        new_value={"copia": target.label},
        request=request,
    )
    _enqueue(tasks.restore_test, kind="manual", user_id=request.user.pk)
    messages.success(
        request,
        f"Teste de restauração da cópia {target.label} pedido; o resultado aparece nesta página.",
    )
    return redirect("operations:panel")


def _qualify(request, kind):
    if not qualification.can_execute(request.user, kind):
        reason = (
            IT_ONLY
            if kind == QualificationKind.INSTALLATION
            else "só a TI e a Garantia da Qualidade executam a qualificação de operação"
        )
        return deny_access(request, reason)
    record_event(
        "operations.qualification_requested",
        actor=request.user,
        object_type="operations.qualificationrun",
        object_id="",
        object_repr=QualificationKind(kind).label,
        new_value={"tipo": kind, "canal": "screen"},
        request=request,
    )
    _enqueue(tasks.qualification, kind=kind, user_id=request.user.pk)
    messages.success(
        request,
        f"{QualificationKind(kind).label} pedida; o relatório aparece nesta página ao terminar.",
    )
    return redirect("operations:panel")


@require_POST
def qualify_installation(request):
    return _qualify(request, QualificationKind.INSTALLATION)


@require_POST
def qualify_operation(request):
    return _qualify(request, QualificationKind.OPERATION)


@require_GET
def report(request, pk):
    if not VIEWERS & _profiles(request):
        return deny_access(request, VIEW_ONLY)
    run = get_object_or_404(QualificationRun.objects.select_related("report"), pk=pk)
    data = read_verified(run.report)
    record_event(
        "operations.report_downloaded",
        actor=request.user,
        obj=run,
        new_value={"relatorio_sha256": run.report.sha256},
        request=request,
    )
    response = FileResponse(iter([data]), content_type="application/pdf")
    response["Content-Disposition"] = content_disposition_header(
        as_attachment=True, filename=run.report.original_name
    )
    return response


@require_GET
def access_review_export(request):
    if not access_review.can_view(request.user):
        return deny_access(request, VIEW_ONLY)
    try:
        name, content_type, data = access_review.export(
            request.GET.get("formato", ""), by=request.user, request=request
        )
    except ValidationError as exc:
        for text in exc.messages:
            messages.error(request, text)
        return redirect("operations:panel")
    response = HttpResponse(data, content_type=content_type)
    response["Content-Disposition"] = content_disposition_header(as_attachment=True, filename=name)
    return response
