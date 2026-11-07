"""Exportação da trilha em CSV e XLSX (contrato exportacao-trilha.md)."""

import csv
import io

from django.http import HttpResponse, StreamingHttpResponse
from django.utils import timezone
from openpyxl import Workbook

from sgp.core.formatting import compact_json, local_datetime

from .event_types import label_for

TITLE = "Trilha de auditoria — SGP-P&D"
HEADER = [
    "Sequência",
    "Data e hora",
    "Usuário",
    "Tipo de evento",
    "Código do tipo",
    "Objeto",
    "ID do objeto",
    "Projeto",
    "Valor anterior",
    "Valor novo",
    "Motivo",
    "Origem",
    "Hash",
]
UTF8_BOM = chr(0xFEFF)
XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def identification_rows(exported_by, filters: str, count: int, exported_at) -> list[list]:
    return [
        [TITLE],
        ["Exportado em", local_datetime(exported_at)],
        ["Exportado por", f"{exported_by.username} — {exported_by.get_full_name()}"],
        ["Filtros", filters],
        ["Eventos", count],
        [],
    ]


def event_row(event) -> list:
    return [
        event.seq,
        local_datetime(event.occurred_at),
        event.actor_username,
        label_for(event.event_type),
        event.event_type,
        event.object_repr or event.object_type,
        event.object_id,
        event.project_id if event.project_id is not None else "",
        compact_json(event.old_value),
        compact_json(event.new_value),
        event.reason,
        event.ip_address,
        event.hash,
    ]


def filename(extension: str, moment=None) -> str:
    moment = timezone.localtime(moment or timezone.now())
    return f"trilha-auditoria-{moment:%Y%m%d-%H%M%S}.{extension}"


class _Echo:
    def write(self, value):
        return value


def csv_response(
    queryset, *, exported_by, filters: str, count: int, exported_at
) -> StreamingHttpResponse:
    writer = csv.writer(_Echo(), delimiter=";", lineterminator="\r\n")

    def rows():
        yield UTF8_BOM
        for row in identification_rows(exported_by, filters, count, exported_at):
            yield writer.writerow(row)
        yield writer.writerow(HEADER)
        for event in queryset.iterator(chunk_size=2000):
            yield writer.writerow(event_row(event))

    response = StreamingHttpResponse(rows(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename("csv", exported_at)}"'
    return response


def xlsx_response(queryset, *, exported_by, filters: str, count: int, exported_at) -> HttpResponse:
    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet("Trilha")
    for row in identification_rows(exported_by, filters, count, exported_at):
        sheet.append(row)
    sheet.append(HEADER)
    for event in queryset.iterator(chunk_size=2000):
        sheet.append(event_row(event))
    buffer = io.BytesIO()
    workbook.save(buffer)
    response = HttpResponse(buffer.getvalue(), content_type=XLSX_CONTENT_TYPE)
    response["Content-Disposition"] = f'attachment; filename="{filename("xlsx", exported_at)}"'
    return response
