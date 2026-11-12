"""Teste de restauração da cópia mais recente — contrato copia-e-manifesto.md da feature 014."""

from django.core.management.base import BaseCommand, CommandError

from sgp.operations.models import RestoreStatus, RunKind
from sgp.operations.restore import RestoreBusy, run_restore_test


class Command(BaseCommand):
    help = "Restaura a cópia mais recente num banco isolado e confere C1 a C6 (descarta o banco)."

    def handle(self, *args, **options):
        try:
            test = run_restore_test(kind=RunKind.MANUAL)
        except RestoreBusy as exc:
            raise CommandError(str(exc)) from exc
        for check in test.checks:
            mark = "aprovada" if check["aprovado"] else "REPROVADA"
            self.stdout.write(
                f"{check['codigo']} {mark} — {check['descricao']}: {check['detalhe']}"
            )
        if test.status != RestoreStatus.PASSED:
            raise CommandError(f"Teste de restauração reprovado: {test.error}")
        self.stdout.write(self.style.SUCCESS("Teste de restauração aprovado."))
