"""Aprovações registradas na trilha geram mensagens de integração na mesma transação."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from sgp.audit.models import AuditEvent

SOURCES = frozenset({"projects.approved", "signatures.approved", "studies.locked"})


@receiver(post_save, sender=AuditEvent, dispatch_uid="integrations_from_audit")
def outbox_from_event(sender, instance, created, **kwargs):
    if not created or instance.event_type not in SOURCES:
        return
    from .services import from_event

    from_event(instance)
