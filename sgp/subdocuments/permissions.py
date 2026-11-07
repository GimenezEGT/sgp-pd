"""Quem vê, cria, edita, aprova e migra subdocumentos (FR-008, FR-014, FR-015 da feature 004)."""

from sgp.accounts.profiles import Profile, active_profiles
from sgp.core.access import can_access_project
from sgp.projects.models import ProjectStatus

MEMBER_EDITORS = frozenset({Profile.ANALYST, Profile.PROJECT_LEADER})


def can_view(user, project) -> bool:
    return can_access_project(user, project)


def can_edit(user, project) -> bool:
    """Membros com perfil Analista/Líder e o Gestor de P&D, em projeto aberto."""
    if project.status != ProjectStatus.OPEN or not can_access_project(user, project):
        return False
    profiles = active_profiles(user)
    if Profile.RD_MANAGER in profiles:
        return True
    return bool(profiles & MEMBER_EDITORS) and project.is_member(user)


def is_manager(user) -> bool:
    return Profile.RD_MANAGER in active_profiles(user)


def can_approve(user, subdocument) -> bool:
    return (
        is_manager(user)
        and subdocument.created_by_id != user.pk
        and can_access_project(user, subdocument.project)
    )


def subdocument_file_policy(user, stored) -> bool:
    """Anexo de subdocumento: entregue a quem acessa o projeto do documento que o anexou."""
    from .models import Subdocument

    candidates = Subdocument.objects.filter(data__contains={"files": [stored.pk]}).select_related(
        "project"
    )
    return any(can_access_project(user, sub.project) for sub in candidates)
