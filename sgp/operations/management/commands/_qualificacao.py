"""Base dos comandos de qualificação (canal "linha de comando")."""

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.management.base import BaseCommand, CommandError

from sgp.accounts.profiles import Profile, active_profiles
from sgp.operations.checks import RESULT_LABELS
from sgp.operations.models import QualificationChannel
from sgp.operations.qualification import execute


class QualificationCommand(BaseCommand):
    kind = ""

    def add_arguments(self, parser):
        parser.add_argument(
            "--usuario",
            required=True,
            help="Login de rede da pessoa da TI que executa (perfil Administrador do sistema).",
        )

    def handle(self, *args, **options):
        user = get_user_model().objects.filter(username=options["usuario"], is_active=True).first()
        if user is None:
            raise CommandError(f"Pessoa ativa {options['usuario']} não encontrada.")
        if Profile.ADMIN not in active_profiles(user):
            raise CommandError(
                "A linha de comando é da TI (perfil Administrador do sistema); a Garantia da "
                "Qualidade executa a qualificação de operação pela tela."
            )
        try:
            run = execute(self.kind, by=user, channel=QualificationChannel.COMMAND)
        except PermissionDenied as exc:
            raise CommandError(str(exc)) from exc
        for item in run.items:
            label = RESULT_LABELS.get(item["resultado"], item["resultado"])
            self.stdout.write(f"{item['codigo']} {label} — {item['descricao']}: {item['detalhe']}")
        self.stdout.write(
            f"Relatório guardado: {run.report.original_name} (SHA-256 {run.report.sha256})."
        )
        if not run.passed:
            raise CommandError(f"{run.get_kind_display()} reprovada.")
        self.stdout.write(self.style.SUCCESS(f"{run.get_kind_display()} aprovada."))
