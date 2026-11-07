"""Regra única de acesso a projetos (FR-014 da feature 001).

Gestor de P&D, Qualidade/AR e Administrador acessam todos os projetos; os demais perfis só os
projetos de que são membros. O objeto de projeto informa a participação por `is_member(user)`.
"""

from sgp.accounts.profiles import GLOBAL_PROJECT_ACCESS, active_profiles


def can_access_project(user, project) -> bool:
    if user is None or not getattr(user, "is_authenticated", False) or not user.is_active:
        return False
    profiles = active_profiles(user)
    if not profiles:
        return False
    if profiles & GLOBAL_PROJECT_ACCESS:
        return True
    is_member = getattr(project, "is_member", None)
    return bool(callable(is_member) and is_member(user))
