"""Preferências e notificações por e-mail (data-model.md da feature 010)."""

from django.conf import settings
from django.db import models
from django.utils import timezone

from sgp.core.models import ProtectedModel

USER = settings.AUTH_USER_MODEL


class NotificationKind(models.TextChoices):
    RETURNED = "returned", "Documento devolvido"
    APPROVED = "approved", "Documento aprovado"
    STALLED = "stalled", "Documento parado na revisão"
    PENDING_SIGNATURE = "pending_signature", "Assinatura pendente"


# Assinatura pendente nunca pode ser desligada (regra da feature 010).
DISABLEABLE = (NotificationKind.RETURNED, NotificationKind.APPROVED, NotificationKind.STALLED)


class NotificationStatus(models.TextChoices):
    PENDING = "pending", "Na fila"
    SENT = "sent", "Enviada"
    FAILED = "failed", "Falhou"
    SKIPPED = "skipped", "Omitida"


class NotificationPreference(ProtectedModel):
    user = models.ForeignKey(
        USER, on_delete=models.PROTECT, related_name="notification_preferences"
    )
    kind = models.CharField("tipo", max_length=20, choices=NotificationKind.choices)
    enabled = models.BooleanField("ligada", default=True)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "preferência de notificação"
        verbose_name_plural = "preferências de notificação"
        constraints = [
            models.UniqueConstraint(fields=["user", "kind"], name="notifications_preference_unique")
        ]


class Notification(ProtectedModel):
    user = models.ForeignKey(USER, on_delete=models.PROTECT, related_name="notifications")
    kind = models.CharField("tipo", max_length=20, choices=NotificationKind.choices)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    project = models.ForeignKey(
        "projects.Project", on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    subject = models.CharField("assunto", max_length=255)
    body = models.TextField("texto")
    dedup_key = models.CharField(max_length=200, unique=True)
    status = models.CharField(
        max_length=10, choices=NotificationStatus.choices, default=NotificationStatus.PENDING
    )
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    sent_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(blank=True)

    class Meta:
        verbose_name = "notificação"
        verbose_name_plural = "notificações"
        ordering = ["-created_at", "-pk"]
        indexes = [models.Index(fields=["user", "-created_at"], name="notifications_user_idx")]

    def __str__(self) -> str:
        return self.subject
