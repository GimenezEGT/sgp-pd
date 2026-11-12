"""Cópia de segurança imediata (mesmo serviço da tarefa diária) — contrato copia-e-manifesto.md."""

from django.core.management.base import BaseCommand, CommandError

from sgp.operations.backup import BackupBusy, run_backup
from sgp.operations.models import BackupStatus, RunKind


class Command(BaseCommand):
    help = "Faz uma cópia de segurança do banco e dos arquivos no destino configurado (BACKUP_DIR)."

    def handle(self, *args, **options):
        try:
            record = run_backup(kind=RunKind.MANUAL)
        except BackupBusy as exc:
            raise CommandError(str(exc)) from exc
        if record.status != BackupStatus.SUCCESS:
            raise CommandError(f"Cópia {record.label or record.pk} falhou: {record.error}")
        self.stdout.write(
            self.style.SUCCESS(
                f"Cópia {record.label} concluída: banco {record.database_size_display}, "
                f"{record.files_total} arquivo(s) ({record.files_new} novo(s)), "
                f"manifesto {record.manifest_sha256}."
            )
        )
