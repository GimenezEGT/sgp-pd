"""Perfis do SGP-P&D e controle de permissão por perfil (FR-009, FR-015 da feature 001)."""

from functools import wraps

from django.db import models
from django.shortcuts import render


class Profile(models.TextChoices):
    ADMIN = "ADMIN", "Administrador do sistema"
    RD_MANAGER = "RD_MANAGER", "Gestor de P&D"
    PROJECT_LEADER = "PROJECT_LEADER", "Líder de projeto"
    ANALYST = "ANALYST", "Analista/Pesquisador"
    QUALITY = "QUALITY", "Qualidade/Assuntos Regulatórios"
    READER = "READER", "Leitor"


# Perfis que acessam todos os projetos (FR-014); os demais só como membros do projeto.
GLOBAL_PROJECT_ACCESS = frozenset({Profile.ADMIN, Profile.RD_MANAGER, Profile.QUALITY})
# Consulta e exportação da trilha (FR-023, FR-024).
AUDIT_TRAIL_PROFILES = frozenset({Profile.QUALITY, Profile.RD_MANAGER, Profile.ADMIN})
# Verificação de integridade sob demanda e alerta de quebra (FR-021, FR-022).
INTEGRITY_PROFILES = frozenset({Profile.QUALITY, Profile.ADMIN})

# Aprovador esperado de cada perfil (Clarifications 2026-11-07; provisório).
EXPECTED_APPROVER = {
    Profile.ADMIN: "gestão da TI",
    Profile.RD_MANAGER: "Gestor de P&D",
    Profile.PROJECT_LEADER: "Gestor de P&D",
    Profile.ANALYST: "Gestor de P&D",
    Profile.QUALITY: "Garantia da Qualidade",
    Profile.READER: "Gestor de P&D",
}

_CACHE_ATTR = "_sgp_active_profiles"


def active_profiles(user, *, refresh: bool = False) -> frozenset:
    """Perfis ativos da pessoa; vazio para anônimo ou pessoa desativada."""
    if user is None or not getattr(user, "is_authenticated", False):
        return frozenset()
    if not getattr(user, "is_active", False):
        return frozenset()
    if not refresh:
        cached = getattr(user, _CACHE_ATTR, None)
        if cached is not None:
            return cached
    from .models import ProfileAssignment

    profiles = frozenset(
        ProfileAssignment.objects.filter(user_id=user.pk, revoked_at__isnull=True).values_list(
            "profile", flat=True
        )
    )
    setattr(user, _CACHE_ATTR, profiles)
    return profiles


def clear_profile_cache(user) -> None:
    if user is not None and hasattr(user, _CACHE_ATTR):
        delattr(user, _CACHE_ATTR)


def has_profile(user, *profiles) -> bool:
    return bool(active_profiles(user) & frozenset(profiles))


def deny_access(request, reason: str):
    """Recusa com 403 e registra a tentativa (a resposta não desfaz o evento)."""
    from sgp.audit.services import record_event

    record_event(
        "auth.permission_denied",
        object_type="route",
        object_id=request.path[:64],
        object_repr=request.path[:255],
        new_value={"rota": request.path, "metodo": request.method, "motivo": reason},
        request=request,
    )
    return render(request, "403.html", status=403)


def profile_required(*profiles):
    allowed = frozenset(profiles)
    labels = ", ".join(Profile(code).label for code in sorted(allowed))

    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if active_profiles(request.user) & allowed:
                return view(request, *args, **kwargs)
            return deny_access(request, f"perfil exigido: {labels}")

        wrapper.sgp_required_profiles = allowed
        return wrapper

    return decorator


def allow_without_profile(view):
    """Marca a view como acessível por pessoa autenticada sem perfil (FR-003)."""
    view.sgp_allow_without_profile = True
    return view
