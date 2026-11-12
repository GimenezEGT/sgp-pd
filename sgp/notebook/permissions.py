"""Quem vê, cria, edita, assina, testemunha e mantém modelos do caderno (research R12)."""

from sgp.accounts.profiles import Profile, active_profiles
from sgp.core.access import can_access_project
from sgp.subdocuments.permissions import can_edit as can_edit_project

from .models import EntryStatus

TEMPLATE_PROFILES = frozenset({Profile.QUALITY, Profile.RD_MANAGER})


def is_manager(user) -> bool:
    return Profile.RD_MANAGER in active_profiles(user)


def can_view(user, project) -> bool:
    """Equipe do projeto, Gestor de P&D, Qualidade/AR e Administrador (regra única da 001)."""
    return can_access_project(user, project)


def can_create(user, project) -> bool:
    """Membros com perfil Analista/Pesquisador ou Líder e o Gestor de P&D, em projeto aberto."""
    return can_edit_project(user, project)


def can_edit_entry(user, entry) -> bool:
    return (
        entry.status == EntryStatus.OPEN
        and entry.author_id == user.pk
        and can_edit_project(user, entry.project)
    )


def can_sign(user, entry) -> bool:
    return can_edit_entry(user, entry)


def witness_refusal(user, entry) -> str:
    """Motivo pelo qual a pessoa não pode testemunhar ('' quando pode)."""
    if not can_access_project(user, entry.project):
        return "sem acesso ao projeto"
    if entry.author_id == user.pk:
        return "o autor não pode testemunhar a própria entrada"
    if not entry.relevant:
        return "só entrada marcada como relevante recebe testemunha"
    if entry.status != EntryStatus.SIGNED:
        return "a entrada precisa estar assinada pelo autor e sem testemunha"
    return ""


def can_witness(user, entry) -> bool:
    return not witness_refusal(user, entry)


def can_mark_relevant(user, entry) -> bool:
    if entry.status == EntryStatus.WITNESSED or not can_access_project(user, entry.project):
        return False
    if is_manager(user):
        return True
    return entry.author_id == user.pk and can_edit_project(user, entry.project)


def can_add_addendum(user, entry) -> bool:
    return entry.status != EntryStatus.OPEN and can_edit_project(user, entry.project)


def can_link(user, entry) -> bool:
    return can_edit_project(user, entry.project)


def can_manage_templates(user) -> bool:
    return bool(active_profiles(user) & TEMPLATE_PROFILES)


def notebook_file_policy(user, stored) -> bool:
    """Anexo do caderno: entregue a quem acessa o projeto da entrada que o anexou."""
    from .models import EntryAttachment

    attachments = EntryAttachment.objects.filter(file=stored).select_related("entry__project")
    return any(can_access_project(user, item.entry.project) for item in attachments)
