"""Gera o certificado autoassinado de TESTE do selo (só desenvolvimento; research R3)."""

import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from sgp.documents.testcert import write_pkcs12


class Command(BaseCommand):
    help = (
        "Gera um certificado autoassinado de teste para o selo do PDF oficial, no caminho de "
        "DOCUMENT_SEAL_PKCS12. Recusa rodar com DEBUG desligado."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--forcar", action="store_true", help="substitui o certificado existente"
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Certificado de teste só em desenvolvimento (DEBUG ligado).")
        path = Path(settings.DOCUMENT_SEAL_PKCS12 or "")
        if not settings.DOCUMENT_SEAL_PKCS12 or not settings.DOCUMENT_SEAL_PASSWORD:
            raise CommandError("Defina DOCUMENT_SEAL_PKCS12 e DOCUMENT_SEAL_PASSWORD.")
        if path.exists() and not options["forcar"]:
            self.stdout.write(f"Certificado de teste já existe em {path}.")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        write_pkcs12(
            path,
            settings.DOCUMENT_SEAL_PASSWORD.encode(),
            common_name="Selo de TESTE do SGP-P&D (desenvolvimento)",
            valid_days=365,
            now=datetime.datetime.now(datetime.UTC),
        )
        self.stdout.write(self.style.SUCCESS(f"Certificado de teste gravado em {path}."))
