"""Trilha de auditoria append-only encadeada e verificações de integridade."""

from django.conf import settings
from django.db import models

from sgp.core.models import AppendOnlyModel


class AuditEvent(AppendOnlyModel):
    """Evento da trilha: somente inclusão, sequência sem lacunas, encadeado por SHA-256."""

    seq = models.BigIntegerField("sequência", primary_key=True)
    occurred_at = models.DateTimeField("data e hora")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="usuário",
    )
    actor_username = models.CharField("login do usuário", max_length=150)
    event_type = models.CharField("tipo de evento", max_length=64)
    object_type = models.CharField("tipo do objeto", max_length=100, blank=True)
    object_id = models.CharField("identificação do objeto", max_length=64, blank=True)
    object_repr = models.CharField("objeto", max_length=255, blank=True)
    project_id = models.BigIntegerField("projeto", null=True, blank=True)
    old_value = models.JSONField("valor anterior", null=True, blank=True)
    new_value = models.JSONField("valor novo", null=True, blank=True)
    reason = models.TextField("motivo", blank=True)
    ip_address = models.CharField("origem", max_length=45, blank=True)
    prev_hash = models.CharField("resumo do evento anterior", max_length=64)
    hash = models.CharField("resumo do evento", max_length=64, unique=True)

    class Meta:
        verbose_name = "evento de auditoria"
        verbose_name_plural = "eventos de auditoria"
        ordering = ["seq"]
        indexes = [
            models.Index(fields=["occurred_at"], name="audit_event_when"),
            models.Index(fields=["actor", "occurred_at"], name="audit_event_actor"),
            models.Index(fields=["event_type", "occurred_at"], name="audit_event_type"),
            models.Index(fields=["project_id", "occurred_at"], name="audit_event_project"),
        ]

    def __str__(self) -> str:
        return f"Evento {self.seq} — {self.event_type}"

    def hash_fields(self) -> dict:
        return {
            "seq": self.seq,
            "occurred_at": self.occurred_at,
            "actor_id": self.actor_id,
            "actor_username": self.actor_username,
            "event_type": self.event_type,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "object_repr": self.object_repr,
            "project_id": self.project_id,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "reason": self.reason,
            "ip_address": self.ip_address,
            "prev_hash": self.prev_hash,
        }


class ChainVerification(AppendOnlyModel):
    """Resultado de uma verificação completa da cadeia (ponto de controle incluído)."""

    class Trigger(models.TextChoices):
        SCHEDULED = "scheduled", "Rotina diária"
        MANUAL = "manual", "Sob demanda"

    class Status(models.TextChoices):
        INTACT = "intact", "Íntegra"
        BROKEN = "broken", "Com quebra"

    started_at = models.DateTimeField("início")
    finished_at = models.DateTimeField("fim")
    trigger = models.CharField("origem", max_length=10, choices=Trigger.choices)
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    events_checked = models.BigIntegerField("eventos verificados")
    status = models.CharField("situação", max_length=10, choices=Status.choices)
    head_seq = models.BigIntegerField("último evento verificado", null=True, blank=True)
    head_hash = models.CharField("resumo do último evento", max_length=64, blank=True)
    breaks = models.JSONField("quebras", default=list, blank=True)

    class Meta:
        verbose_name = "verificação de integridade"
        verbose_name_plural = "verificações de integridade"
        ordering = ["-finished_at", "-id"]

    def __str__(self) -> str:
        return f"Verificação de {self.finished_at:%d/%m/%Y %H:%M} — {self.get_status_display()}"
