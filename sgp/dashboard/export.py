"""Exportação da carteira em XLSX (FR-006; research R5)."""

import io

from openpyxl import Workbook
from openpyxl.styles import Font

COLUMNS = [
    ("Projeto", "code"),
    ("Título", "title"),
    ("Produto", "product"),
    ("Líder", "leader"),
    ("Etapa atual", "stage"),
    ("Subdocumentos aprovados (%)", "percent"),
    ("Marcos planejados", "milestones_planned"),
    ("Marcos realizados", "milestones_done"),
    ("Atraso (dias)", "delay"),
    ("Entradas do caderno atrasadas", "notebook_overdue"),
]
FINANCIAL_COLUMNS = [("Custo planejado", "cost"), ("Retorno esperado (5 anos)", "return")]


def workbook(rows: list[dict]) -> bytes:
    columns = list(COLUMNS)
    if any(row["financial"] for row in rows):
        columns += FINANCIAL_COLUMNS
    book = Workbook()
    sheet = book.active
    sheet.title = "Carteira"
    sheet.append([label for label, _ in columns])
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for row in rows:
        values = []
        for _, key in columns:
            value = row.get(key)
            if key in ("cost", "return") and not row["financial"]:
                value = ""
            if key == "delay" and value is None:
                value = "sem marcos"
            values.append(value)
        sheet.append(values)
    for column in sheet.columns:
        width = max(len(str(cell.value or "")) for cell in column)
        sheet.column_dimensions[column[0].column_letter].width = min(max(width + 2, 10), 60)
    buffer = io.BytesIO()
    book.save(buffer)
    return buffer.getvalue()
