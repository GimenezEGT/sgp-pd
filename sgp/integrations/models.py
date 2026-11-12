"""Mapeamento e mensagens de integração (data-model.md da feature 012)."""

from django.conf import settings
from django.db import models
from django.utils import timezone

from sgp.core.models import AppendOnlyModel, ProtectedModel

USER = settings.AUTH_USER_MODEL


class IntegrationMapping(AppendOnlyModel):
    version = models.PositiveIntegerField("versão", unique=True)
    yaml = models.TextField("mapeamento (YAML)")
    parsed = models.JSONField("mapeamento normalizado")
    note = models.CharField("observação", max_length=500, blank=True)
    created_by = models.ForeignKey(USER, on_delete=models.PROTECT, null=True, related_name="+")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-version"]

    def __str__(self) -> str:
        return f"Mapeamento do Sankhya – versão {self.version}"


class MessageStatus(models.TextChoices):
    PENDING = "pending", "Na fila"
    WAITING_CONFIG = "waiting_config", "Aguardando configuração"
    SENT = "sent", "Enviada"
    ERROR = "error", "Erro"


class IntegrationMessage(ProtectedModel):
    record_type = models.CharField("registro", max_length=20)
    idempotency_key = models.CharField("chave de idempotência", max_length=120, unique=True)
    record_key = models.CharField(
        "chave do registro no Sankhya",
        max_length=120,
        blank=True,
        help_text="Vazia: a própria chave de idempotência (uma mensagem por registro).",
    )
    project = models.ForeignKey(
        "projects.Project", on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    payload = models.JSONField("conteúdo")
    status = models.CharField(
        max_length=16, choices=MessageStatus.choices, default=MessageStatus.PENDING
    )
    attempts = models.PositiveSmallIntegerField(default=0)
    last_error = models.TextField(blank=True)
    next_attempt_at = models.DateTimeField(null=True, blank=True)
    mapping_version = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        indexes = [
            models.Index(fields=["status", "next_attempt_at"], name="integrations_due_idx"),
            models.Index(fields=["record_type", "-created_at"], name="integrations_type_idx"),
        ]

    @property
    def target_key(self) -> str:
        """Chave do registro no Sankhya: a do registro atualizado ou a da própria mensagem."""
        return self.record_key or self.idempotency_key

    def __str__(self) -> str:
        return f"{self.idempotency_key} ({self.get_status_display()})"
