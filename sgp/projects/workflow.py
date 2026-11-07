"""Máquina de estados do projeto e geração do código anual (FR-011 a FR-016)."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.utils import timezone

from sgp.accounts.profiles import Profile, active_profiles
from sgp.audit.services import record_event

from .completeness import pending_items
from .models import DecisionAction, Project, ProjectDecision, ProjectStatus

SUBMIT, APPROVE, RETURN = "submit", "approve", "return"

TRANSITIONS = {
    (SUBMIT, ProjectStatus.DRAFT): ProjectStatus.SUBMITTED,
    (SUBMIT, ProjectStatus.RETURNED): ProjectStatus.SUBMITTED,
    (APPROVE, ProjectStatus.SUBMITTED): ProjectStatus.OPEN,
    (RETURN, ProjectStatus.SUBMITTED): ProjectStatus.RETURNED,
}

ACTION_LABELS = {SUBMIT: "submeter", APPROVE: "aprovar", RETURN: "devolver"}


class PendingItemsError(ValidationError):
    """Submissão recusada por pendências; `messages` traz a lista."""


def target_status(action: str, status: str) -> str:
    try:
        return TRANSITIONS[(action, status)]
    except KeyError as exc:
        raise ValidationError(
            f"Não é possível {ACTION_LABELS.get(action, action)} um projeto na situação "
            f"{ProjectStatus(status).label}."
        ) from exc


def next_project_code(year: int | None = None) -> str:
    """Próximo código do ano numa só instrução atômica (sem colisão entre aprovações)."""
    year = year or timezone.localdate().year
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO projects_projectcodesequence (year, last_value) VALUES (%s, 1) "
            "ON CONFLICT (year) DO UPDATE SET last_value = projects_projectcodesequence.last_value + 1 "
            "RETURNING last_value",
            [year],
        )
        number = cursor.fetchone()[0]
    return f"{settings.PROJECT_CODE_PREFIX}-{year}-{number:03d}"


def _lock(project: Project) -> Project:
    return Project.objects.select_for_update().get(pk=project.pk)


def _decide(project: Project, action: str, by, comment: str = "") -> None:
    ProjectDecision.objects.create(project=project, action=action, actor=by, comment=comment)


def submit(project: Project, *, by) -> Project:
    with transaction.atomic():
        project = _lock(project)
        if project.leader_id != by.pk:
            raise ValidationError("Só o líder do projeto pode submetê-lo.")
        previous = project.status
        target = target_status(SUBMIT, previous)
        pending = pending_items(project)
        if pending:
            raise PendingItemsError(pending)
        project.status = target
        project.submitted_at = timezone.now()
        project.save(update_fields=["status", "submitted_at", "updated_at"])
        _decide(project, DecisionAction.SUBMITTED, by)
        record_event(
            "projects.submitted",
            actor=by,
            obj=project,
            project_id=project.pk,
            old_value={"situacao": previous},
            new_value={"situacao": target},
        )
    return project


def _check_decider(project: Project, by) -> None:
    if Profile.RD_MANAGER not in active_profiles(by):
        raise ValidationError("Só o Gestor de P&D aprova ou devolve projetos.")
    if project.leader_id == by.pk:
        raise ValidationError("O líder do projeto não pode aprovar nem devolver o próprio projeto.")


def return_project(project: Project, *, by, comment: str) -> Project:
    comment = (comment or "").strip()
    if not comment:
        raise ValidationError("Informe o comentário da devolução.")
    with transaction.atomic():
        project = _lock(project)
        _check_decider(project, by)
        target = target_status(RETURN, project.status)
        project.status = target
        project.save(update_fields=["status", "updated_at"])
        _decide(project, DecisionAction.RETURNED, by, comment)
        record_event(
            "projects.returned",
            actor=by,
            obj=project,
            project_id=project.pk,
            old_value={"situacao": ProjectStatus.SUBMITTED},
            new_value={"situacao": target},
            reason=comment,
        )
    return project


def approve(project: Project, *, by) -> Project:
    with transaction.atomic():
        project = _lock(project)
        _check_decider(project, by)
        target = target_status(APPROVE, project.status)
        project.code = next_project_code()
        project.version = 1
        project.status = target
        project.approved_at = timezone.now()
        project.approved_by = by
        project.save(
            update_fields=["code", "version", "status", "approved_at", "approved_by", "updated_at"]
        )
        _decide(project, DecisionAction.APPROVED, by)
        record_event(
            "projects.approved",
            actor=by,
            obj=project,
            project_id=project.pk,
            old_value={"situacao": ProjectStatus.SUBMITTED},
            new_value={
                "situacao": target,
                "codigo": project.code,
                "versao": project.version_display,
            },
        )
    return project
