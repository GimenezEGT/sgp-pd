"""Qualificação de instalação (IQ) pela linha de comando — FR-011 da feature 014."""

from sgp.operations.models import QualificationKind

from ._qualificacao import QualificationCommand


class Command(QualificationCommand):
    help = "Confere a instalação e guarda o relatório em PDF (IQ)."
    kind = QualificationKind.INSTALLATION
