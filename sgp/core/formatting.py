"""Formatação de valores para tela e exportação (padrão brasileiro)."""

import json
from decimal import ROUND_HALF_UP, Decimal

from django.utils import timezone

DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"
DATE_FORMAT = "%d/%m/%Y"


def local_datetime(value) -> str:
    if value is None:
        return ""
    return timezone.localtime(value).strftime(DATETIME_FORMAT)


def local_date(value) -> str:
    if value is None:
        return ""
    return value.strftime(DATE_FORMAT)


def compact_json(value) -> str:
    if value is None or value == "":
        return ""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(", ", ": "))


def format_decimal_br(value, places: int = 2) -> str:
    """1234567.891 → '1.234.567,89' (meio para cima; a regra por estudo chega na feature 007)."""
    if value is None or value == "":
        return ""
    quantum = Decimal(1).scaleb(-places) if places else Decimal(1)
    number = Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP)
    sign = "-" if number < 0 else ""
    text = f"{abs(number):.{places}f}"
    integer, _, fraction = text.partition(".")
    grouped = f"{int(integer):,}".replace(",", ".")
    return f"{sign}{grouped},{fraction}" if places else f"{sign}{grouped}"


def format_brl(value) -> str:
    if value is None or value == "":
        return ""
    text = format_decimal_br(value, 2)
    if text.startswith("-"):
        return f"-R$ {text[1:]}"
    return f"R$ {text}"


def format_int_br(value) -> str:
    if value is None or value == "":
        return ""
    return format_decimal_br(value, 0)
