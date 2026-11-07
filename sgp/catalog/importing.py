"""Importação de insumos por planilha CSV ou XLSX (FR-013; contrato importacao-insumos.md).

Fluxo: o arquivo é lido e validado linha a linha; a pré-visualização grava só a importação
(com o arquivo e o resultado de cada linha) e nenhum insumo. Na confirmação, as linhas válidas
são revalidadas (o código pode ter sido ocupado nesse meio-tempo) e só então criadas, cada uma
com o seu evento na trilha. O relatório de rejeições sai das linhas rejeitadas.
"""

import csv
import io
import os
import unicodedata

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from sgp.audit.services import record_event
from sgp.files.storage import SPREADSHEET_KINDS, ZIP_SIGNATURE, check_upload, store_upload

from .kinds import MATERIALS
from .models import ImportBatch, ImportStatus, Material, MaterialType
from .versioning import create_record

UTF8_BOM = chr(0xFEFF)
MAX_ROWS = 5000
COLUMNS = ("codigo", "descricao", "tipo", "fabricante", "lote_fabricante", "novo")
REQUIRED = ("codigo", "descricao", "tipo")
LIMITS = {"codigo": 40, "descricao": 300, "fabricante": 200, "lote_fabricante": 100}
TYPE_ALIASES = {
    "materia-prima": MaterialType.RAW,
    "materia prima": MaterialType.RAW,
    "mp": MaterialType.RAW,
    "embalagem": MaterialType.PACKAGING,
    "material de embalagem": MaterialType.PACKAGING,
    "me": MaterialType.PACKAGING,
}
TRUE_VALUES = {"sim", "s", "1", "true"}
FALSE_VALUES = {"nao", "n", "0", "false", ""}
REPORT_HEADER = ("linha", "codigo", "descricao", "motivos")


def normalize(text) -> str:
    """Sem acento, sem diferença de caixa e com espaços simples."""
    text = unicodedata.normalize("NFKD", str(text or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.lower().split())


def header_key(text) -> str:
    return normalize(text).replace(" ", "_").replace("-", "_")


def _cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value).strip()


def _decode(content: bytes) -> str:
    if content.startswith(UTF8_BOM.encode("utf-8")):
        return content.decode("utf-8-sig")
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("latin-1")


def _read_csv(content: bytes) -> list[list[str]]:
    text = _decode(content)
    first_line = text.split("\n", 1)[0]
    delimiter = ";" if first_line.count(";") >= first_line.count(",") else ","
    return [
        [_cell(value) for value in row]
        for row in csv.reader(io.StringIO(text, newline=""), delimiter=delimiter)
    ]


def _read_xlsx(content: bytes) -> list[list[str]]:
    from openpyxl import load_workbook

    try:
        workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception as exc:  # arquivo corrompido ou não é planilha
        raise ValidationError("Não foi possível ler a planilha XLSX.") from exc
    try:
        sheet = workbook.worksheets[0]
        return [[_cell(value) for value in row] for row in sheet.iter_rows(values_only=True)]
    finally:
        workbook.close()


def read_table(name: str, content: bytes) -> tuple[list[str], list[tuple[int, dict]]]:
    """Lê o arquivo e devolve o cabeçalho normalizado e as linhas (número da linha, valores)."""
    if name.lower().endswith(".xlsx") or content.startswith(ZIP_SIGNATURE):
        table = _read_xlsx(content)
    else:
        table = _read_csv(content)
    while table and not any(table[0]):
        table.pop(0)
    if not table:
        raise ValidationError("A planilha está vazia.")
    header = [header_key(value) for value in table[0]]
    missing = [column for column in REQUIRED if column not in header]
    if missing:
        raise ValidationError(
            "A planilha não segue o layout: faltam as colunas "
            f"{', '.join(missing)}. Colunas esperadas: {'; '.join(COLUMNS)}."
        )
    rows = []
    for number, values in enumerate(table[1:], start=2):
        if not any(values):
            continue
        row = {}
        for index, key in enumerate(header):
            if key in COLUMNS and key not in row:
                row[key] = values[index] if index < len(values) else ""
        rows.append((number, row))
    if len(rows) > MAX_ROWS:
        raise ValidationError(
            f"A planilha tem {len(rows)} linhas; o limite é {MAX_ROWS:,} por arquivo.".replace(
                ",", "."
            )
        )
    return header, rows


def _validate_row(row: dict, seen: dict, existing: set) -> tuple[dict, list[str]]:
    errors = []
    code = row.get("codigo", "").strip()
    description = " ".join(row.get("descricao", "").split())
    if not code:
        errors.append("código vazio")
    elif any(char.isspace() for char in code):
        errors.append("código com espaços")
    elif code in seen:
        errors.append(f"código repetido na planilha (linha {seen[code]})")
    elif code in existing:
        errors.append("código já cadastrado")
    if not description:
        errors.append("descrição vazia")
    for column, limit in LIMITS.items():
        value = row.get(column, "")
        if len(value) > limit:
            errors.append(f"{column} passa de {limit} caracteres")
    raw_type = row.get("tipo", "")
    material_type = TYPE_ALIASES.get(normalize(raw_type))
    if material_type is None:
        errors.append(
            f"tipo inválido: {raw_type!r} (use matéria-prima ou material de embalagem)"
            if raw_type
            else "tipo vazio"
        )
    raw_new = normalize(row.get("novo", ""))
    if raw_new in TRUE_VALUES:
        new_to_company = True
    elif raw_new in FALSE_VALUES:
        new_to_company = False
    else:
        new_to_company = False
        errors.append(f"valor inválido em novo: {row.get('novo')!r} (use sim ou não)")
    data = {
        "codigo": code,
        "descricao": description,
        "tipo": material_type.value if material_type else raw_type,
        "fabricante": row.get("fabricante", "").strip(),
        "lote_fabricante": row.get("lote_fabricante", "").strip(),
        "novo": new_to_company,
    }
    return data, errors


def validate_rows(rows: list[tuple[int, dict]]) -> list[dict]:
    codes = {row.get("codigo", "").strip() for _, row in rows}
    existing = set(Material.objects.current().filter(code__in=codes).values_list("code", flat=True))
    seen: dict[str, int] = {}
    result = []
    for number, row in rows:
        data, errors = _validate_row(row, seen, existing)
        if data["codigo"] and data["codigo"] not in seen:
            seen[data["codigo"]] = number
        result.append({"linha": number, "dados": data, "erros": errors})
    return result


def preview(uploaded, *, by) -> ImportBatch:
    """Valida a planilha e grava a importação em pré-visualização, sem criar insumos."""
    check_upload(uploaded, SPREADSHEET_KINDS)
    uploaded.seek(0)
    content = uploaded.read()
    _, rows = read_table(os.path.basename(uploaded.name), content)
    results = validate_rows(rows)
    rejected = sum(1 for row in results if row["erros"])
    with transaction.atomic():
        stored = store_upload(uploaded, by=by, allowed=SPREADSHEET_KINDS)
        batch = ImportBatch.objects.create(
            source_file=stored,
            uploaded_by=by,
            rows=results,
            valid_count=len(results) - rejected,
            rejected_count=rejected,
        )
        record_event(
            "catalog.import_previewed",
            actor=by,
            obj=batch,
            new_value={
                "arquivo": stored.original_name,
                "linhas": len(results),
                "validas": batch.valid_count,
                "rejeitadas": rejected,
            },
        )
    return batch


def confirm(batch: ImportBatch, *, by) -> ImportBatch:
    """Cria os insumos das linhas válidas, revalidando o código de cada uma."""
    with transaction.atomic():
        batch = ImportBatch.objects.select_for_update().get(pk=batch.pk)
        if batch.status == ImportStatus.CONFIRMED:
            raise ValidationError("Esta importação já foi confirmada.")
        rows = batch.rows
        valid = [row for row in rows if not row["erros"]]
        taken = set(
            Material.objects.current()
            .filter(code__in=[row["dados"]["codigo"] for row in valid])
            .values_list("code", flat=True)
        )
        created = 0
        for row in valid:
            data = row["dados"]
            if data["codigo"] in taken:
                row["erros"] = ["código cadastrado depois da pré-visualização"]
                continue
            create_record(
                MATERIALS,
                by=by,
                data={
                    "code": data["codigo"],
                    "description": data["descricao"],
                    "material_type": data["tipo"],
                    "manufacturer": data["fabricante"],
                    "manufacturer_lot": data["lote_fabricante"],
                    "new_to_company": data["novo"],
                },
            )
            created += 1
        rejected = sum(1 for row in rows if row["erros"])
        batch.rows = rows
        batch.created_count = created
        batch.valid_count = created
        batch.rejected_count = rejected
        batch.status = ImportStatus.CONFIRMED
        batch.confirmed_at = timezone.now()
        batch.confirmed_by = by
        batch.save()
        record_event(
            "catalog.import_confirmed",
            actor=by,
            obj=batch,
            new_value={"criados": created, "rejeitadas": rejected},
        )
    return batch


def _csv_text(rows) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    for row in rows:
        writer.writerow(row)
    return UTF8_BOM + buffer.getvalue()


def rejection_report(batch: ImportBatch) -> str:
    """CSV `linha;codigo;descricao;motivos` em UTF-8 com BOM (abre direto no Excel)."""
    lines = [REPORT_HEADER]
    for row in batch.rejected_rows():
        data = row["dados"]
        lines.append((row["linha"], data["codigo"], data["descricao"], " | ".join(row["erros"])))
    return _csv_text(lines)


def template_csv() -> str:
    return _csv_text([COLUMNS])
