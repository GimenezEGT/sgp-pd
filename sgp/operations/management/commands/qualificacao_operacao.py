"""Qualificação de operação (OQ) pela linha de comando — FR-012 da feature 014."""

from sgp.operations.models import QualificationKind

from ._qualificacao import QualificationCommand


class Command(QualificationCommand):
    help = "Confere a operação sem alterar dados e guarda o relatório em PDF (OQ)."
    kind = QualificationKind.OPERATION
