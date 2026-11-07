"""Verificação manual (ou por cron da TI) da integridade da trilha; sai com código 1 se houver quebra."""

import sys

from django.core.management.base import BaseCommand

from sgp.audit.models import ChainVerification
from sgp.audit.services import break_label, verify_chain


class Command(BaseCommand):
    help = "Verifica a integridade da cadeia de eventos da trilha de auditoria."

    def add_arguments(self, parser):
        parser.add_argument(
            "--agendada",
            action="store_true",
            help="registra a execução como rotina agendada (cron) em vez de sob demanda",
        )

    def handle(self, *args, **options):
        trigger = (
            ChainVerification.Trigger.SCHEDULED
            if options["agendada"]
            else ChainVerification.Trigger.MANUAL
        )
        result = verify_chain(trigger=trigger)
        self.stdout.write(
            f"Situação: {result.get_status_display()} · eventos verificados: {result.events_checked} · "
            f"último evento: {result.head_seq} · resumo: {result.head_hash}"
        )
        for item in result.breaks:
            self.stdout.write(
                f"  evento {item['seq']}: {break_label(item['kind'])} — {item['detail']}"
            )
        if result.status == ChainVerification.Status.BROKEN:
            sys.exit(1)
