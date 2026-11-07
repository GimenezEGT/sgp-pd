"""Acesso, edição e dados financeiros de projetos (FR-003, FR-010, FR-014)."""

from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404

from sgp.accounts.profiles import GLOBAL_PROJECT_ACCESS, Profile, active_profiles, deny_access
from sgp.core.access import can_access_project

from .models import Project, ProjectMember, ProjectStatus

CREATE_PROFILES = frozenset({Profile.PROJECT_LEADER, Profile.RD_MANAGER})
FINANCIAL_FIELDS = (
    "total_cost",
    "forecasts",
    "forecast_total",
    "competitor_price_min",
    "competitor_price_max",
    "max_production_cost",
    "sale_price_min",
    "sale_price_max",
    "annual_sales_tests",
)


def accessible_projects(user):
    """Projetos que a pessoa acessa pela regra única (perfil global, líder ou membro ativo)."""
    queryset = Project.objects.select_related("leader", "technology", "business_plan")
    if active_profiles(user) & GLOBAL_PROJECT_ACCESS:
        return queryset
    member_projects = (
        ProjectMember.objects.active()
        .filter(user=user, project__status=ProjectStatus.OPEN)
        .values("project_id")
    )
    return queryset.filter(Q(leader=user) | Q(pk__in=member_projects))


def is_leader(user, project: Project) -> bool:
    return (
        bool(getattr(user, "is_authenticated", False))
        and project.leader_id == user.pk
        and bool(active_profiles(user))
    )


def can_view_financials(user, project: Project | None) -> bool:
    profiles = active_profiles(user)
    if not profiles:
        return False
    if Profile.RD_MANAGER in profiles:
        return True
    if project is not None and project.leader_id == user.pk:
        return True
    allowed = set(getattr(settings, "FINANCIAL_DATA_PROFILES", ()) or ())
    return bool(profiles & allowed)


def can_edit_documents(user, project: Project) -> bool:
    return is_leader(user, project) and project.status in {
        ProjectStatus.DRAFT,
        ProjectStatus.RETURNED,
    }


def can_manage_team(user, project: Project) -> bool:
    return is_leader(user, project) and project.status != ProjectStatus.SUBMITTED


def can_decide(user, project: Project) -> bool:
    from sgp.signatures.services import is_approver

    return is_approver(user) and project.leader_id != user.pk


def get_project_or_deny(request, project_id):
    """Carrega o projeto ou devolve (None, resposta 403 registrada)."""
    project = get_object_or_404(
        Project.objects.select_related("technology", "leader", "created_by", "approved_by"),
        pk=project_id,
    )
    if not can_access_project(request.user, project):
        return None, deny_access(request, "sem acesso ao projeto")
    return project, None


def financial_viewer_rule(viewer, project_id, cache: dict) -> bool:
    """Regra de mascaramento da trilha para os eventos do Plano de Negócios."""
    if project_id is None:
        return can_view_financials(viewer, None)
    if project_id not in cache:
        cache[project_id] = Project.objects.filter(pk=project_id).only("id", "leader_id").first()
    return can_view_financials(viewer, cache[project_id])
