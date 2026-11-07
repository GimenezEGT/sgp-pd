"""Reautenticação na assinatura, tentativas e bloqueio (FR-006 e FR-008 da feature 005).

A senha é conferida no diretório da rede pelo mesmo backend do login e nunca é guardada. A
terceira falha seguida cria um bloqueio temporário e o evento de alerta. Diretório indisponível
recusa a assinatura sem contar como falha.

Importante: chame `reauthenticate` fora de blocos `transaction.atomic()` do serviço, para que as
tentativas e eventos de falha não sejam desfeitos junto com a operação recusada.
"""

from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.db.models import Max
from django.utils import timezone

from sgp.accounts import ldap as sgp_ldap
from sgp.audit.services import record_event
from sgp.core.formatting import local_datetime

from .models import SignatureAttempt, SignatureLock


class SignatureError(ValidationError):
    """Assinatura recusada (senha, bloqueio ou diretório indisponível)."""


def active_lock(user) -> SignatureLock | None:
    return SignatureLock.objects.filter(user=user, expires_at__gt=timezone.now()).first()


def consecutive_failures(user) -> int:
    last_success = SignatureAttempt.objects.filter(user=user, success=True).aggregate(at=Max("at"))[
        "at"
    ]
    last_lock = SignatureLock.objects.filter(user=user).aggregate(at=Max("created_at"))["at"]
    since = max(filter(None, [last_success, last_lock]), default=None)
    failures = SignatureAttempt.objects.filter(user=user, success=False)
    if since is not None:
        failures = failures.filter(at__gt=since)
    return failures.count()


def _user_event(event_type: str, user, **kwargs):
    return record_event(
        event_type,
        actor=user,
        object_type="accounts.user",
        object_id=str(user.pk),
        object_repr=user.username,
        **kwargs,
    )


def reauthenticate(request, user, password: str) -> None:
    lock = active_lock(user)
    if lock is not None:
        raise SignatureError(
            f"Assinatura bloqueada até {local_datetime(lock.expires_at)} por falhas de senha."
        )
    if not password:
        raise SignatureError("Informe a sua senha de rede para assinar.")
    sgp_ldap.reset_unavailable()
    authenticated = authenticate(request, username=user.username, password=password)
    if authenticated is None and sgp_ldap.was_unavailable():
        raise SignatureError(
            "O diretório da rede está indisponível; tente assinar de novo em instantes."
        )
    if authenticated is None or authenticated.pk != user.pk:
        SignatureAttempt.objects.create(user=user, success=False, reason="senha")
        failures = consecutive_failures(user)
        _user_event("signatures.failed", user, new_value={"tentativas_seguidas": failures})
        if failures >= settings.SIGNATURE_MAX_FAILURES:
            lock = SignatureLock.objects.create(
                user=user,
                expires_at=timezone.now() + timedelta(minutes=settings.SIGNATURE_LOCK_MINUTES),
            )
            _user_event("signatures.blocked", user, new_value={"bloqueado_ate": lock.expires_at})
            raise SignatureError(
                "Senha incorreta pela terceira vez seguida: a assinatura ficou bloqueada até "
                f"{local_datetime(lock.expires_at)}."
            )
        raise SignatureError("Senha de rede incorreta.")
    SignatureAttempt.objects.create(user=user, success=True)
