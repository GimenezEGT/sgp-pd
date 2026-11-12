"""Eventos da trilha que geram e-mail imediato (devolução e aprovação de documento)."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from sgp.audit.models import AuditEvent

IMMEDIATE = frozenset(
    {"signatures.returned", "signatures.approved", "projects.returned", "projects.approved"}
)


@receiver(post_save, sender=AuditEvent, dispatch_uid="notifications_from_audit")
def notify_from_event(sender, instance, created, **kwargs):
    if not created or instance.event_type not in IMMEDIATE:
        return
    from .services import notify_event

    notify_event(instance)
