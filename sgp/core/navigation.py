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
        "Projetos",
        "projects:list",
        frozenset(Profile),
        "Projetos",
        "Abrir projetos, preencher TAP e Plano de Negócios, acompanhar aprovações.",
    ),
    NavItem(
        "Verificar documento",
        "documents:verify",
        frozenset(Profile),
        "Projetos",
        "Conferir pelo código de verificação um documento oficial gerado pelo sistema.",
    ),
    NavItem(
        "Painel de projetos",
        "dashboard:portfolio",
        frozenset(Profile),
        "Projetos",
        "Carteira com etapa, aprovados, marcos e atraso; exportação em planilha.",
    ),
    NavItem(
        "Minhas pendências",
        "dashboard:pending",
        frozenset(Profile),
        "Projetos",
        "O que está com você: aprovar, corrigir, assinar e testemunhar.",
    ),
    NavItem(
        "Notificações por e-mail",
        "notifications:preferences",
        frozenset(Profile),
        "Projetos",
        "Escolha os e-mails que quer receber; assinatura pendente é sempre enviada.",
    ),
    NavItem(
        "Caderno de laboratório",
        "notebook:search",
        frozenset(Profile),
        "Projetos",
        "Entradas de experimentos dos projetos, com busca, pendências de assinatura e testemunha.",
    ),
    NavItem(
        "Fila de revisão",
        "signatures:queue",
        frozenset({Profile.RD_MANAGER}),
        "Projetos",
        "Documentos aguardando a sua aprovação, com os dias de espera.",
    ),
    NavItem(
        "Modelos de formulário",
        "formtemplates:list",
        frozenset(Profile),
        "Cadastros",
        "Modelos dos subdocumentos do PSG 20, com versões e vigência.",
    ),
    NavItem(
        "Revisões de modelos",
        "revisions:list",
        frozenset(Profile),
        "Cadastros",
        "Revisões de modelos em andamento, aprovação assinada pelo Gestor e retiradas de uso.",
    ),
    NavItem(
        "Modelos de layout",
        "layouts:list",
        frozenset(Profile),
        "Cadastros",
        "Capa, cabeçalho, rodapé e estilos dos documentos gerados, com versões e vigência.",
    ),
    NavItem(
        "Modelos de entrada do caderno",
        "notebook:templates",
        frozenset(Profile),
        "Cadastros",
        "Textos de partida por tipo de experimento, mantidos pela Qualidade/AR e pelo Gestor.",
    ),
    NavItem(
        "Cadastros",
        "catalog:index",
        frozenset(Profile),
        "Cadastros",
        "Lotes, insumos, kits de referência, amostras, painéis, normas e referências.",
    ),
    NavItem(
        "Listas controladas",
        "vocab:lists",
        frozenset({Profile.QUALITY}),
        "Cadastros",
        "Tipos de amostra, armazenamento, tecnologias e tipos de subdocumento.",
    ),
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
