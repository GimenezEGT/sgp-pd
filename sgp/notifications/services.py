"""Criar, enviar e resumir notificações; preferências por pessoa (feature 010, research R7 e R8)."""

import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from sgp.audit.services import record_event

from . import recipients
from .models import (
    DISABLEABLE,
    Notification,
    NotificationKind,
    NotificationPreference,
    NotificationStatus,
)

logger = logging.getLogger(__name__)
MAX_ATTEMPTS = 3
PREFIX = "[SGP-P&D]"


def site_url(path: str = "") -> str:
    return settings.SITE_URL.rstrip("/") + path


def is_enabled(user, kind: str) -> bool:
    if kind not in DISABLEABLE:
        return True
    preference = NotificationPreference.objects.filter(user=user, kind=kind).first()
    return preference is None or preference.enabled


def preferences(user) -> list[dict]:
    rows = []
    for kind, label in NotificationKind.choices:
        rows.append(
            {
                "kind": kind,
                "label": label,
                "enabled": is_enabled(user, kind),
                "locked": kind not in DISABLEABLE,
            }
        )
    return rows


def set_preferences(user, enabled_kinds) -> None:
    enabled_kinds = set(enabled_kinds)
    before = {kind: is_enabled(user, kind) for kind in DISABLEABLE}
    after = {kind: kind in enabled_kinds for kind in DISABLEABLE}
    if before == after:
        return
    with transaction.atomic():
        for kind, enabled in after.items():
            NotificationPreference.objects.update_or_create(
                user=user, kind=kind, defaults={"enabled": enabled, "updated_at": timezone.now()}
            )
        record_event(
            "notifications.preference_changed",
            actor=user,
            object_type="accounts.user",
            object_id=str(user.pk),
            object_repr=user.username,
            old_value=before,
            new_value=after,
        )


def _skip(notification: Notification, reason: str) -> None:
    notification.status = NotificationStatus.SKIPPED
    notification.error = reason
    notification.save(update_fields=["status", "error"])
    record_event(
        "notifications.skipped",
        actor=None,
        obj=notification,
        project_id=notification.project_id,
        new_value={"destinatario": notification.user.username, "tipo": notification.kind},
        reason=reason,
    )


def create(
    user,
    kind: str,
    *,
    subject: str,
    body: str,
    dedup_key: str,
    project=None,
    object_type: str = "",
    object_id: str = "",
    object_repr: str = "",
) -> Notification | None:
    """Cria a notificação (uma por chave); a omitida fica registrada com o motivo."""
    if Notification.objects.filter(dedup_key=dedup_key).exists():
        return None
    try:
        with transaction.atomic():
            notification = Notification.objects.create(
                user=user,
                kind=kind,
                subject=subject[:255],
                body=body,
                dedup_key=dedup_key[:200],
                project=project,
                object_type=object_type[:100],
                object_id=str(object_id)[:64],
                object_repr=object_repr[:255],
            )
    except IntegrityError:
        return None
    if not is_enabled(user, kind):
        _skip(notification, "Tipo de notificação desligado pela pessoa.")
    elif not (user.email or "").strip():
        _skip(notification, "Pessoa sem e-mail cadastrado.")
    else:
        from .tasks import send as send_task

        transaction.on_commit(lambda: send_task.delay(notification.pk))
    return notification


def send(notification_id: int) -> Notification:
    """Envia com até 3 tentativas; falha fica registrada e a pendência continua na tela."""
    notification = Notification.objects.select_related("user").get(pk=notification_id)
    if notification.status != NotificationStatus.PENDING:
        return notification
    error = ""
    while notification.attempts < MAX_ATTEMPTS:
        notification.attempts += 1
        try:
            send_mail(
                notification.subject,
                notification.body,
                settings.DEFAULT_FROM_EMAIL,
                [notification.user.email],
                fail_silently=False,
            )
        except Exception as exc:  # noqa: BLE001 - SMTP pode falhar de várias formas
            error = f"{exc.__class__.__name__}: {exc}"[:500]
            logger.warning("Falha no envio da notificação %s: %s", notification.pk, error)
            continue
        notification.status = NotificationStatus.SENT
        notification.sent_at = timezone.now()
        notification.error = ""
        with transaction.atomic():
            notification.save(update_fields=["status", "sent_at", "error", "attempts"])
            record_event(
                "notifications.sent",
                actor=None,
                obj=notification,
                project_id=notification.project_id,
                new_value={
                    "destinatario": notification.user.username,
                    "tipo": notification.kind,
                    "tentativas": notification.attempts,
                },
            )
        return notification
    notification.status = NotificationStatus.FAILED
    notification.error = error
    with transaction.atomic():
        notification.save(update_fields=["status", "error", "attempts"])
        record_event(
            "notifications.failed",
            actor=None,
            obj=notification,
            project_id=notification.project_id,
            new_value={"destinatario": notification.user.username, "tipo": notification.kind},
            reason=error,
        )
    return notification


# ------------------------------------------------------------------ e-mails imediatos

KIND_BY_OBJECT = {
    "signatures.subdocument": "subdocument",
    "signatures.charter": "charter",
    "signatures.business_plan": "business_plan",
}


def _document_body(action: str, label: str, project, event, url: str) -> str:
    lines = [
        f"{label}",
        f"Projeto: {project}",
        f"{action} por {event.actor_username} em "
        f"{timezone.localtime(event.occurred_at).strftime('%d/%m/%Y %H:%M')}.",
    ]
    if event.reason:
        lines.append(f"Comentário: {event.reason}")
    lines += ["", f"Abra no SGP-P&D: {url}", "", "Mensagem automática do SGP-P&D."]
    return "\n".join(lines)


def _object_url(kind: str, obj, project) -> str:
    if kind == "subdocument":
        return site_url(reverse("subdocuments:detail", args=[obj.pk]))
    return site_url(reverse("projects:detail", args=[project.pk]))


def notify_event(event) -> None:
    """Devolução e aprovação geram e-mail imediato (contrato notificacoes.md)."""
    from sgp.projects.models import Project

    returned = event.event_type in ("signatures.returned", "projects.returned")
    kind = NotificationKind.RETURNED if returned else NotificationKind.APPROVED
    action = "Devolvido" if returned else "Aprovado"
    if event.object_type in KIND_BY_OBJECT:
        doc_kind = KIND_BY_OBJECT[event.object_type]
        obj, project, label = recipients.document(doc_kind, event.object_id)
        if obj is None:
            return
        people = (
            recipients.for_returned(doc_kind, obj)
            if returned
            else recipients.for_approved(doc_kind, obj)
        )
        url = _object_url(doc_kind, obj, project)
    elif event.object_type == "projects.project":
        project = Project.objects.select_related("leader").filter(pk=event.object_id).first()
        if project is None:
            return
        label = f"Projeto {project}"
        people = [project.leader]
        url = site_url(reverse("projects:detail", args=[project.pk]))
    else:
        return
    subject = f"{PREFIX} {NotificationKind(kind).label}: {label}"
    body = _document_body(action, label, project, event, url)
    for person in people:
        create(
            person,
            kind,
            subject=subject,
            body=body,
            dedup_key=f"evento:{event.seq}:{person.pk}",
            project=project,
            object_type=event.object_type,
            object_id=event.object_id,
            object_repr=event.object_repr,
        )


# ------------------------------------------------------------------ resumo diário


def _approvers():
    from sgp.accounts.models import User
    from sgp.signatures.services import is_approver

    return [user for user in User.objects.filter(is_active=True) if is_approver(user)]


def digest_items(now=None) -> dict:
    """Itens vencidos por pessoa: {pessoa: [(tipo, texto, url)]} (contrato notificacoes.md)."""
    from sgp.notebook.models import EntryStatus, NotebookEntry
    from sgp.signatures.services import review_queue

    now = now or timezone.now()
    today = timezone.localtime(now).date()
    items: dict = {}

    def add(user, kind, text, url):
        if user is None or not user.is_active:
            return
        items.setdefault(user, []).append((kind, text, url))

    elaborators_seen = set()
    for approver in _approvers():
        for row in review_queue(approver):
            days = (today - timezone.localtime(row["since"]).date()).days
            if days <= settings.REVIEW_ALERT_DAYS:
                continue
            url = _object_url(row["kind"], row["obj"], row["project"])
            add(
                approver,
                NotificationKind.PENDING_SIGNATURE,
                f"Aprovar {row['title']} ({row['project']}): em revisão há {days} dia(s).",
                url,
            )
            key = (row["kind"], row["obj"].pk)
            if key not in elaborators_seen:
                elaborators_seen.add(key)
                add(
                    recipients.elaborator(row["kind"], row["obj"]),
                    NotificationKind.STALLED,
                    f"{row['title']} ({row['project']}) está em revisão há {days} dia(s).",
                    url,
                )
    limit_days = int(getattr(settings, "NOTEBOOK_SIGN_DAYS", 7))
    moment = now - timedelta(days=limit_days)
    entries = NotebookEntry.objects.select_related("author", "project__leader")
    for entry in entries.filter(status=EntryStatus.OPEN, created_at__lt=moment):
        days = (now - entry.created_at).days
        add(
            entry.author,
            NotificationKind.PENDING_SIGNATURE,
            f"Assinar a entrada {entry.number} do caderno {entry.project.code} "
            f"({entry.title}): aberta há {days} dia(s).",
            site_url(reverse("notebook:detail", args=[entry.pk])),
        )
    for entry in entries.filter(status=EntryStatus.SIGNED, relevant=True, signed_at__lt=moment):
        days = (now - entry.signed_at).days
        add(
            entry.project.leader,
            NotificationKind.PENDING_SIGNATURE,
            f"Providenciar testemunha da entrada {entry.number} do caderno {entry.project.code} "
            f"({entry.title}): aguardando há {days} dia(s).",
            site_url(reverse("notebook:detail", args=[entry.pk])),
        )
    return items


def daily_digest(now=None) -> list[Notification]:
    now = now or timezone.now()
    today = timezone.localtime(now).date()
    created = []
    for user, entries in digest_items(now).items():
        allowed = [item for item in entries if is_enabled(user, item[0])]
        if not allowed:
            continue
        pending = any(kind == NotificationKind.PENDING_SIGNATURE for kind, _, _ in allowed)
        kind = NotificationKind.PENDING_SIGNATURE if pending else NotificationKind.STALLED
        lines = [f"Pendências vencidas em {today.strftime('%d/%m/%Y')}:", ""]
        for _, text, url in allowed:
            lines += [f"- {text}", f"  {url}"]
        lines += [
            "",
            f"Minhas pendências: {site_url(reverse('dashboard:pending'))}",
            "",
            "Mensagem automática do SGP-P&D (resumo diário).",
        ]
        notification = create(
            user,
            kind,
            subject=f"{PREFIX} Resumo diário de pendências ({len(allowed)})",
            body="\n".join(lines),
            dedup_key=f"resumo:{user.pk}:{today.isoformat()}",
        )
        if notification is not None:
            created.append(notification)
    return created
