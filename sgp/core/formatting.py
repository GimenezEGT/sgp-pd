"""Formatação de valores para tela e exportação (padrão brasileiro)."""

import json

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
