"""Itens de navegação por perfil. Features novas acrescentam itens em NAV_ITEMS."""

from dataclasses import dataclass

from django.urls import NoReverseMatch, reverse

from sgp.accounts.profiles import (
    AUDIT_TRAIL_PROFILES,
    INTEGRITY_PROFILES,
    Profile,
)


@dataclass(frozen=True)
class NavItem:
    label: str
    url_name: str
    profiles: frozenset
    section: str
    description: str = ""


NAV_ITEMS: list[NavItem] = [
    NavItem(
        "Pessoas e perfis",
        "accounts:people",
        frozenset({Profile.ADMIN}),
        "Administração",
        "Conceder e revogar perfis, com motivo e aprovação.",
    ),
    NavItem(
        "Solicitações de acesso",
        "accounts:access_requests",
        frozenset({Profile.ADMIN}),
        "Administração",
        "Pedidos de quem entrou sem perfil.",
    ),
    NavItem(
        "Bloqueios de login",
        "accounts:lockouts",
        frozenset({Profile.ADMIN}),
        "Administração",
        "Logins bloqueados por tentativas inválidas.",
    ),
    NavItem(
        "Trilha de auditoria",
        "audit:trail",
        frozenset(AUDIT_TRAIL_PROFILES),
        "Auditoria",
        "Consultar e exportar os eventos registrados.",
    ),
    NavItem(
        "Integridade da trilha",
        "audit:integrity",
        frozenset(INTEGRITY_PROFILES),
        "Auditoria",
        "Verificar se a cadeia de eventos foi adulterada.",
    ),
]


def nav_for(profiles: frozenset, current_view: str | None = None) -> list[dict]:
    items = []
    for item in NAV_ITEMS:
        if not (item.profiles & profiles):
            continue
        try:
            url = reverse(item.url_name)
        except NoReverseMatch:
            continue
        items.append(
            {
                "label": item.label,
                "url": url,
                "section": item.section,
                "description": item.description,
                "active": current_view == item.url_name,
            }
        )
    return items
