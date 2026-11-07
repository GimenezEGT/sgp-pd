"""Designa o primeiro Administrador do sistema na implantação (procedimento da TI)."""

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from sgp.accounts.models import ProfileAssignment, User, normalize_username
from sgp.accounts.profiles import Profile
from sgp.accounts.services import grant_profile
from sgp.audit.services import record_event


class Command(BaseCommand):
    help = (
        "Concede o perfil Administrador à primeira pessoa (só quando não há Administrador ativo)."
    )

    def add_arguments(self, parser):
        parser.add_argument("username", help="login de rede da pessoa")
        parser.add_argument("--motivo", required=True, help="motivo da designação")
        parser.add_argument(
            "--aprovacao", required=True, help="referência da aprovação da gestão da TI"
        )

    def handle(self, *args, **options):
        username = normalize_username(options["username"])
        if not username:
            raise CommandError("Informe o login de rede.")
        exists = ProfileAssignment.objects.filter(
            profile=Profile.ADMIN, revoked_at__isnull=True, user__is_active=True
        ).exists()
        if exists:
            raise CommandError(
                "Já existe Administrador ativo; conceda perfis em Administração › Pessoas e perfis."
            )
        with transaction.atomic():
            user, created = User.objects.get_or_create(username=username)
            if created:
                record_event(
                    "accounts.user_created",
                    actor=None,
                    obj=user,
                    new_value={"username": username},
                    reason="Pré-cadastro na implantação; dados da rede entram no primeiro login",
                )
            try:
                grant_profile(
                    user,
                    Profile.ADMIN,
                    by=None,
                    reason=options["motivo"],
                    approval_reference=options["aprovacao"],
                )
            except ValidationError as exc:
                raise CommandError(" ".join(exc.messages)) from exc
        self.stdout.write(self.style.SUCCESS(f"Perfil Administrador concedido a {username}."))
