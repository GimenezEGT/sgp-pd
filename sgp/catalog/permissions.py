"""Quem consulta e quem edita os cadastros (FR-008, FR-009 da feature 003).

Todos os perfis consultam; Analista/Pesquisador, Líder de projeto, Gestor de P&D e
Qualidade/AR cadastram e corrigem. Lotes pertencem a um projeto e seguem a regra única de
acesso a projetos (sgp.core.access).
"""

from sgp.accounts.profiles import Profile, active_profiles
from sgp.core.access import can_access_project
from sgp.projects.models import ProjectStatus
from sgp.projects.permissions import accessible_projects

EDITOR_PROFILES = frozenset(
    {Profile.ANALYST, Profile.PROJECT_LEADER, Profile.RD_MANAGER, Profile.QUALITY}
)


def can_edit_catalog(user) -> bool:
    return bool(active_profiles(user) & EDITOR_PROFILES)


def can_view_record(user, record) -> bool:
    if not active_profiles(user):
        return False
    project = getattr(record, "project", None)
    if project is not None:
        return can_access_project(user, project)
    return True


def can_edit_record(user, record) -> bool:
    return can_edit_catalog(user) and can_view_record(user, record)


def lot_projects(user):
    """Projetos em que a pessoa pode cadastrar lotes: acessíveis e abertos."""
    return accessible_projects(user).filter(status=ProjectStatus.OPEN).order_by("code")


def visible_lot_projects(user):
    return accessible_projects(user)
