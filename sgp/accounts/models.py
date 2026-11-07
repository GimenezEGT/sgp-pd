"""Pessoas, concessões de perfil, solicitações de acesso, tentativas e bloqueios de login."""

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.db.models import Q
from django.utils import timezone

from sgp.core.models import AppendOnlyModel, ProtectedModel, ProtectedQuerySet

from .profiles import Profile


def normalize_username(value: str | None) -> str:
    return (value or "").strip().lower()[:150]


class UserQuerySet(ProtectedQuerySet):
    pass


class UserManager(BaseUserManager.from_queryset(UserQuerySet)):
    use_in_migrations = True

    def get_by_natural_key(self, username):
        return self.get(username=normalize_username(username))

    def create_user(self, username, **extra_fields):
        user = self.model(username=normalize_username(username), **extra_fields)
        user.set_unusable_password()
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, ProtectedModel):
    """Pessoa que entrou ao menos uma vez com a conta de rede (a senha nunca é guardada)."""

    username = models.CharField("login de rede", max_length=150, unique=True)
    full_name = models.CharField("nome", max_length=255, blank=True)
    first_name = models.CharField("nome próprio", max_length=150, blank=True)
    last_name = models.CharField("sobrenome", max_length=150, blank=True)
    email = models.EmailField("e-mail", max_length=254, blank=True)
    job_title = models.CharField("função", max_length=255, blank=True)
    is_active = models.BooleanField("ativa", default=True)
    created_at = models.DateTimeField("cadastrada em", default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "pessoa"
        verbose_name_plural = "pessoas"
        ordering = ["username"]

    def save(self, *args, **kwargs):
        self.username = normalize_username(self.username)
        for name in ("full_name", "first_name", "last_name", "job_title", "email"):
            value = getattr(self, name) or ""
            setattr(self, name, value[: self._meta.get_field(name).max_length])
        if not self.password:
            self.set_unusable_password()
        super().save(*args, **kwargs)

    def get_full_name(self) -> str:
        composed = " ".join(part for part in (self.first_name, self.last_name) if part)
        return self.full_name or composed or self.username

    def get_short_name(self) -> str:
        return self.first_name or self.username

    def __str__(self) -> str:
        return f"{self.get_full_name()} ({self.username})"


class ProfileAssignment(ProtectedModel):
    """Concessão de perfil; a revogação encerra a concessão, que nunca é apagada."""

    class Source(models.TextChoices):
        MANUAL = "manual", "Manual"
        NETWORK_GROUP = "network_group", "Grupo da rede"

    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="profile_assignments")
    profile = models.CharField("perfil", max_length=20, choices=Profile.choices)
    source = models.CharField(
        "origem", max_length=20, choices=Source.choices, default=Source.MANUAL
    )
    source_group = models.CharField("grupo da rede", max_length=500, blank=True)
    granted_at = models.DateTimeField("concedido em", default=timezone.now)
    granted_by = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    grant_reason = models.TextField("motivo da concessão")
    approval_reference = models.CharField("referência da aprovação", max_length=500, blank=True)
    revoked_at = models.DateTimeField("revogado em", null=True, blank=True)
    revoked_by = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    revoke_reason = models.TextField("motivo da revogação", blank=True)

    class Meta:
        verbose_name = "concessão de perfil"
        verbose_name_plural = "concessões de perfil"
        ordering = ["-granted_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "profile"],
                condition=Q(revoked_at__isnull=True),
                name="accounts_unique_active_profile",
            )
        ]

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None

    def __str__(self) -> str:
        return f"{self.get_profile_display()} - {self.user.username}"


class AccessRequest(ProtectedModel):
    """Pedido de acesso de quem entrou sem perfil (FR-003, FR-016)."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        GRANTED = "granted", "Atendida"
        REJECTED = "rejected", "Recusada"

    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="access_requests")
    justification = models.TextField("justificativa")
    created_at = models.DateTimeField("solicitada em", default=timezone.now)
    status = models.CharField(
        "situação", max_length=10, choices=Status.choices, default=Status.PENDING
    )
    decided_at = models.DateTimeField("decidida em", null=True, blank=True)
    decided_by = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    decision_reason = models.TextField("motivo da decisão", blank=True)

    class Meta:
        verbose_name = "solicitação de acesso"
        verbose_name_plural = "solicitações de acesso"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"Solicitação de {self.user.username} em {self.created_at:%d/%m/%Y}"


class LoginAttempt(AppendOnlyModel):
    """Tentativa de login (somente inclusão); base do bloqueio por tentativas."""

    class Result(models.TextChoices):
        SUCCESS = "success", "Aceita"
        FAILURE = "failure", "Recusada"
        BLOCKED = "blocked", "Bloqueada"
        UNAVAILABLE = "unavailable", "Serviço indisponível"

    username = models.CharField("login informado", max_length=150)
    user = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, blank=True, related_name="login_attempts"
    )
    attempted_at = models.DateTimeField("data e hora", default=timezone.now)
    result = models.CharField("resultado", max_length=12, choices=Result.choices)
    ip_address = models.CharField("origem", max_length=45, blank=True)

    class Meta:
        verbose_name = "tentativa de login"
        verbose_name_plural = "tentativas de login"
        ordering = ["-attempted_at", "-id"]
        indexes = [
            models.Index(
                fields=["username", "result", "attempted_at"], name="accounts_attempt_lookup"
            )
        ]


class LoginLockout(ProtectedModel):
    """Bloqueio de login por tentativas inválidas seguidas (FR-006, FR-007)."""

    username = models.CharField("login bloqueado", max_length=150, db_index=True)
    started_at = models.DateTimeField("início", default=timezone.now)
    expires_at = models.DateTimeField("fim previsto")
    failure_count = models.PositiveIntegerField("tentativas inválidas")
    released_at = models.DateTimeField("desbloqueado em", null=True, blank=True)
    released_by = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    release_reason = models.TextField("motivo do desbloqueio", blank=True)

    class Meta:
        verbose_name = "bloqueio de login"
        verbose_name_plural = "bloqueios de login"
        ordering = ["-started_at", "-id"]

    @property
    def is_active(self) -> bool:
        return self.released_at is None and self.expires_at > timezone.now()

    def __str__(self) -> str:
        return f"Bloqueio de {self.username}"
