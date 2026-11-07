"""Regras de login, bloqueio, perfis e solicitações de acesso (feature 001).

Toda mudança grava o evento de auditoria na mesma transação (FR-018).
"""

import logging
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Max
from django.utils import timezone

from sgp.audit.services import ANONYMOUS, record_event
from sgp.core.formatting import local_datetime
from sgp.core.request_context import client_ip

from . import ldap as sgp_ldap
from .models import (
    AccessRequest,
    LoginAttempt,
    LoginLockout,
    ProfileAssignment,
    User,
    normalize_username,
)
from .profiles import Profile, active_profiles, clear_profile_cache

logger = logging.getLogger(__name__)

GENERIC_LOGIN_ERROR = "Usuário ou senha inválidos."
UNAVAILABLE_ERROR = "Serviço de autenticação indisponível. Tente novamente ou acione a TI."
LOCKED_ERROR = (
    "Login bloqueado por excesso de tentativas inválidas até {hora}. "
    "Tente novamente depois desse horário ou procure o Administrador do sistema."
)

USER_FIELDS = ("full_name", "first_name", "last_name", "email", "job_title", "is_active")


@dataclass
class LoginResult:
    status: str
    user: User | None = None
    message: str = ""
    has_profile: bool = False


# --------------------------------------------------------------------------- login


def _snapshot(user: User | None) -> dict | None:
    if user is None:
        return None
    return {field: getattr(user, field) for field in USER_FIELDS}


def _login_event(event_type: str, username: str, **kwargs):
    return record_event(
        event_type,
        actor=None,
        actor_username=ANONYMOUS,
        object_type="accounts.login",
        object_id=username[:64],
        object_repr=username,
        **kwargs,
    )


def login_flow(request, username: str, password: str) -> LoginResult:
    """Autentica no AD com bloqueio, registro de tentativas e eventos (FR-001 a FR-006)."""
    username = normalize_username(username)
    ip = client_ip(request)
    existing = User.objects.filter(username=username).first()

    lockout = active_lockout(username)
    if lockout is not None:
        LoginAttempt.objects.create(
            username=username, user=existing, result=LoginAttempt.Result.BLOCKED, ip_address=ip
        )
        _login_event(
            "auth.login_blocked", username, new_value={"bloqueado_ate": lockout.expires_at}
        )
        return LoginResult(
            "blocked", message=LOCKED_ERROR.format(hora=local_datetime(lockout.expires_at))
        )

    before = _snapshot(existing)
    sgp_ldap.reset_unavailable()
    user = authenticate(request, username=username, password=password)

    if user is None and sgp_ldap.was_unavailable():
        LoginAttempt.objects.create(
            username=username, user=existing, result=LoginAttempt.Result.UNAVAILABLE, ip_address=ip
        )
        _login_event("auth.auth_unavailable", username)
        return LoginResult("unavailable", message=UNAVAILABLE_ERROR)

    if user is None or not user.is_active:
        LoginAttempt.objects.create(
            username=username, user=existing, result=LoginAttempt.Result.FAILURE, ip_address=ip
        )
        reason = "conta desativada no SGP-P&D" if user is not None else ""
        _login_event("auth.login_failed", username, reason=reason)
        register_failure(username)
        return LoginResult("failure", message=GENERIC_LOGIN_ERROR)

    _record_user_changes(user, before)
    sync_network_profiles(user, sgp_ldap.network_group_dns(user))
    LoginAttempt.objects.create(
        username=username, user=user, result=LoginAttempt.Result.SUCCESS, ip_address=ip
    )
    login(request, user)
    record_event("auth.login_succeeded", actor=user, obj=user)
    return LoginResult("success", user=user, has_profile=bool(active_profiles(user, refresh=True)))


def _record_user_changes(user: User, before: dict | None) -> None:
    after = _snapshot(user)
    if before is None:
        record_event(
            "accounts.user_created",
            actor=None,
            obj=user,
            new_value=after,
            reason="Primeiro login com a conta de rede",
        )
        return
    changed = [field for field in USER_FIELDS if before[field] != after[field]]
    if changed:
        record_event(
            "accounts.user_updated",
            actor=None,
            obj=user,
            old_value={field: before[field] for field in changed},
            new_value={field: after[field] for field in changed},
            reason="Dados atualizados a partir da rede no login",
        )


# ------------------------------------------------------------------------- bloqueio


def active_lockout(username: str) -> LoginLockout | None:
    return (
        LoginLockout.objects.filter(
            username=username, released_at__isnull=True, expires_at__gt=timezone.now()
        )
        .order_by("-started_at")
        .first()
    )


def consecutive_failures(username: str) -> int:
    """Falhas desde o último login aceito ou o início do último bloqueio."""
    last_success = LoginAttempt.objects.filter(
        username=username, result=LoginAttempt.Result.SUCCESS
    ).aggregate(value=Max("attempted_at"))["value"]
    last_lockout = LoginLockout.objects.filter(username=username).aggregate(
        value=Max("started_at")
    )["value"]
    since = max((moment for moment in (last_success, last_lockout) if moment), default=None)
    failures = LoginAttempt.objects.filter(username=username, result=LoginAttempt.Result.FAILURE)
    if since is not None:
        failures = failures.filter(attempted_at__gt=since)
    return failures.count()


def register_failure(username: str) -> LoginLockout | None:
    failures = consecutive_failures(username)
    if failures < settings.LOGIN_MAX_FAILURES:
        return None
    now = timezone.now()
    lockout = LoginLockout.objects.create(
        username=username,
        started_at=now,
        expires_at=now + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES),
        failure_count=failures,
    )
    record_event(
        "auth.lockout_started",
        actor=None,
        actor_username=ANONYMOUS,
        obj=lockout,
        object_repr=username,
        new_value={"falhas": failures, "expira_em": lockout.expires_at},
    )
    return lockout


def release_lockout(lockout: LoginLockout, by: User, reason: str) -> LoginLockout:
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError("Informe o motivo do desbloqueio.")
    with transaction.atomic():
        lockout = LoginLockout.objects.select_for_update().get(pk=lockout.pk)
        if not lockout.is_active:
            raise ValidationError("Este bloqueio não está mais ativo.")
        previous_expiry = lockout.expires_at
        lockout.released_at = timezone.now()
        lockout.released_by = by
        lockout.release_reason = reason
        lockout.save(update_fields=["released_at", "released_by", "release_reason"])
        record_event(
            "auth.lockout_released",
            actor=by,
            obj=lockout,
            object_repr=lockout.username,
            old_value={"expira_em": previous_expiry},
            new_value={"liberado_em": lockout.released_at},
            reason=reason,
        )
    return lockout


# --------------------------------------------------------------------------- perfis


def _active_codes(user: User) -> list[str]:
    clear_profile_cache(user)
    return sorted(active_profiles(user, refresh=True))


def grant_profile(
    user: User,
    profile: str,
    *,
    by: User | None,
    reason: str,
    approval_reference: str = "",
    source: str = ProfileAssignment.Source.MANUAL,
    source_group: str = "",
) -> ProfileAssignment:
    """Concede perfil com motivo e aprovação (FR-010); a origem pode ser grupo da rede (FR-013)."""
    reason = (reason or "").strip()
    approval_reference = (approval_reference or "").strip()
    if profile not in Profile.values:
        raise ValidationError("Perfil inválido.")
    if not reason:
        raise ValidationError("Informe o motivo da concessão.")
    if source == ProfileAssignment.Source.MANUAL and not approval_reference:
        raise ValidationError("Informe a referência da aprovação (quem aprovou e onde).")
    if not User.objects.filter(pk=user.pk, is_active=True).exists():
        raise ValidationError("Pessoa desativada não recebe perfil.")
    try:
        with transaction.atomic():
            before = _active_codes(user)
            if profile in before:
                raise ValidationError("A pessoa já tem esse perfil ativo.")
            assignment = ProfileAssignment.objects.create(
                user=user,
                profile=profile,
                source=source,
                source_group=source_group,
                granted_by=by,
                grant_reason=reason,
                approval_reference=approval_reference,
            )
            record_event(
                "accounts.profile_granted",
                actor=by,
                obj=assignment,
                old_value={"perfis": before},
                new_value={
                    "perfis": sorted([*before, profile]),
                    "perfil": profile,
                    "origem": source,
                    "grupo_da_rede": source_group,
                    "aprovacao": approval_reference,
                },
                reason=reason,
            )
    except IntegrityError as exc:
        raise ValidationError("A pessoa já tem esse perfil ativo.") from exc
    clear_profile_cache(user)
    return assignment


def revoke_profile(
    assignment: ProfileAssignment,
    *,
    by: User | None,
    reason: str,
    approval_reference: str = "",
) -> ProfileAssignment:
    """Revoga sem apagar (FR-011) com motivo e aprovação (FR-010); nunca deixa o sistema sem
    Administrador ativo (FR-012). Revogação pelo sistema (by=None) vem da sincronização."""
    reason = (reason or "").strip()
    approval_reference = (approval_reference or "").strip()
    if not reason:
        raise ValidationError("Informe o motivo da revogação.")
    if by is not None and not approval_reference:
        raise ValidationError("Informe a referência da aprovação da revogação.")
    with transaction.atomic():
        assignment = ProfileAssignment.objects.select_for_update().get(pk=assignment.pk)
        if assignment.revoked_at is not None:
            raise ValidationError("Esta concessão já foi revogada.")
        if assignment.profile == Profile.ADMIN:
            active_admins = list(
                ProfileAssignment.objects.select_for_update()
                .filter(profile=Profile.ADMIN, revoked_at__isnull=True, user__is_active=True)
                .exclude(pk=assignment.pk)
            )
            if not active_admins:
                raise ValidationError(
                    "Não é possível revogar o último Administrador ativo do sistema."
                )
        user = assignment.user
        before = _active_codes(user)
        assignment.revoked_at = timezone.now()
        assignment.revoked_by = by
        assignment.revoke_reason = reason
        assignment.revoke_approval_reference = approval_reference
        assignment.save(
            update_fields=["revoked_at", "revoked_by", "revoke_reason", "revoke_approval_reference"]
        )
        record_event(
            "accounts.profile_revoked",
            actor=by,
            obj=assignment,
            old_value={"perfis": before},
            new_value={
                "perfis": [code for code in before if code != assignment.profile],
                "perfil": assignment.profile,
                "origem": assignment.source,
                "aprovacao": approval_reference,
            },
            reason=reason,
        )
    clear_profile_cache(user)
    return assignment


def sync_network_profiles(user: User, group_dns: set[str]) -> None:
    """Concede/revoga perfis mapeados a grupos da rede; não toca concessões manuais (FR-013)."""
    mapping: dict[str, str] = getattr(settings, "LDAP_PROFILE_GROUPS", {}) or {}
    if not mapping:
        return
    group_dns = {dn.lower() for dn in group_dns}
    active = list(ProfileAssignment.objects.filter(user=user, revoked_at__isnull=True))
    active_codes = {assignment.profile for assignment in active}
    for profile, dn in sorted(mapping.items()):
        if dn in group_dns and profile not in active_codes:
            grant_profile(
                user,
                profile,
                by=None,
                reason=f"Sincronização com o grupo da rede {dn}",
                approval_reference="Pertencimento ao grupo da rede",
                source=ProfileAssignment.Source.NETWORK_GROUP,
                source_group=dn,
            )
    for assignment in active:
        if assignment.source != ProfileAssignment.Source.NETWORK_GROUP:
            continue
        dn = mapping.get(assignment.profile)
        if dn is None or dn not in group_dns:
            try:
                revoke_profile(
                    assignment,
                    by=None,
                    reason=f"Pessoa fora do grupo da rede {assignment.source_group}",
                    approval_reference="Saída do grupo da rede",
                )
            except ValidationError:
                logger.warning(
                    "Perfil %s de %s mantido: é o último Administrador ativo.",
                    assignment.profile,
                    user.username,
                )


# --------------------------------------------------------------------------- pessoas


def set_person_active(person: User, *, by: User, active: bool, reason: str) -> User:
    """Desativa ou reativa a pessoa sem apagar o cadastro (FR-026); nunca desativa o último
    Administrador ativo (FR-012)."""
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError("Informe o motivo.")
    with transaction.atomic():
        person = User.objects.select_for_update().get(pk=person.pk)
        if person.is_active == active:
            raise ValidationError(
                "A pessoa já está ativa." if active else "A pessoa já está desativada."
            )
        if not active:
            is_admin = ProfileAssignment.objects.filter(
                user=person, profile=Profile.ADMIN, revoked_at__isnull=True
            ).exists()
            other_admins = (
                ProfileAssignment.objects.select_for_update()
                .filter(profile=Profile.ADMIN, revoked_at__isnull=True, user__is_active=True)
                .exclude(user=person)
            )
            if is_admin and not list(other_admins):
                raise ValidationError("Não é possível desativar o último Administrador ativo.")
        person.is_active = active
        person.save(update_fields=["is_active"])
        record_event(
            "accounts.user_updated",
            actor=by,
            obj=person,
            old_value={"is_active": not active},
            new_value={"is_active": active},
            reason=reason,
        )
    clear_profile_cache(person)
    return person


# ----------------------------------------------------------- solicitações de acesso


def create_access_request(user: User, justification: str) -> AccessRequest:
    justification = (justification or "").strip()
    if not justification:
        raise ValidationError("Informe a justificativa.")
    with transaction.atomic():
        access_request = AccessRequest.objects.create(user=user, justification=justification)
        record_event(
            "accounts.access_requested",
            actor=user,
            obj=access_request,
            new_value={"justificativa": justification},
        )
    return access_request


def decide_access_request(
    access_request: AccessRequest, *, by: User, decision: str, reason: str
) -> AccessRequest:
    reason = (reason or "").strip()
    if decision not in (AccessRequest.Status.GRANTED, AccessRequest.Status.REJECTED):
        raise ValidationError("Decisão inválida.")
    if not reason:
        raise ValidationError("Informe o motivo da decisão.")
    with transaction.atomic():
        access_request = AccessRequest.objects.select_for_update().get(pk=access_request.pk)
        if access_request.status != AccessRequest.Status.PENDING:
            raise ValidationError("Esta solicitação já foi decidida.")
        access_request.status = decision
        access_request.decided_at = timezone.now()
        access_request.decided_by = by
        access_request.decision_reason = reason
        access_request.save(update_fields=["status", "decided_at", "decided_by", "decision_reason"])
        record_event(
            "accounts.access_request_decided",
            actor=by,
            obj=access_request,
            old_value={"situacao": AccessRequest.Status.PENDING},
            new_value={"situacao": decision},
            reason=reason,
        )
    return access_request
