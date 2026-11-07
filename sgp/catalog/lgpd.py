"""Proteção de dados pessoais nas amostras (FR-015, FR-016 da feature 003; research R6).

As amostras guardam só o código interno e dados analíticos. O identificador precisa seguir o
padrão de código (um nome de pessoa não passa) e os textos recusam CPF, e-mail, telefone e
expressões que indiquem identificação de paciente.
"""

import re

from django.core.exceptions import ValidationError

IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,29}$")
DIGIT = re.compile(r"\d")
CPF = re.compile(r"(?<!\d)\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?!\d)")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
PHONE = re.compile(r"(?<!\d)(\+?55\s?)?\(?\d{2}\)?\s?9?\d{4}[-\s]\d{4}(?!\d)")
PATIENT_WORDS = re.compile(r"\b(pacientes?|nomes?)\b", re.IGNORECASE)

IDENTIFIER_MESSAGE = (
    "Use o código interno da amostra: letras, números, ponto, sublinhado, hífen ou barra, sem espaços, até "
    "30 caracteres e com ao menos um dígito. Nunca use o nome do paciente."
)


def validate_identifier(value: str) -> None:
    value = value or ""
    if not IDENTIFIER_PATTERN.match(value) or not DIGIT.search(value):
        raise ValidationError(IDENTIFIER_MESSAGE)


def personal_data_findings(text: str) -> list[str]:
    text = text or ""
    findings = []
    if CPF.search(text):
        findings.append("CPF")
    if EMAIL.search(text):
        findings.append("e-mail")
    if PHONE.search(text):
        findings.append("telefone")
    if PATIENT_WORDS.search(text):
        findings.append("identificação de paciente")
    return findings


def validate_no_personal_data(value: str) -> None:
    findings = personal_data_findings(value)
    if findings:
        raise ValidationError(
            "Amostras não guardam dados pessoais de pacientes (LGPD): o texto parece conter "
            f"{', '.join(findings)}. Registre só o código interno e dados analíticos."
        )
