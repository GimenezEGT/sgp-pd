"""Avisos por e-mail aos administradores do sistema (FR-008 da feature 014, research R7)."""

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction

from sgp.accounts.profiles import Profile

logger = logging.getLogger(__name__)


def admin_emails() -> list[str]:
    """E-mails das pessoas ativas com o perfil Administrador do sistema vigente."""
    users = (
        get_user_model()
        .objects.filter(
            is_active=True,
            profile_assignments__profile=Profile.ADMIN,
            profile_assignments__revoked_at__isnull=True,
        )
        .exclude(email="")
        .values_list("email", flat=True)
        .distinct()
    )
    return sorted(set(users))


def notify_admins(subject: str, body: str) -> None:
    """Envia depois do commit; falha de envio vai para o log e não desfaz o registro."""

    def _send():
        recipients = admin_emails()
        if not recipients:
            logger.warning("Aviso sem destinatário (nenhum administrador com e-mail): %s", subject)
            return
        try:
            send_mail(
                f"[SGP-P&D] {subject}",
                body,
                settings.DEFAULT_FROM_EMAIL,
                recipients,
            )
        except Exception:  # noqa: BLE001 - o aviso não pode derrubar a cópia nem o teste
            logger.exception("Falha ao enviar o aviso: %s", subject)

    transaction.on_commit(_send)
