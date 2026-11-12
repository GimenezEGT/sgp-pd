"""Importação de medidas por CSV ou XLSX com mapeamento salvo por equipamento (FR-006; R7).

A pré-visualização valida as linhas como a tela (cadastros, números, qualitativos) e vai assinada
para a confirmação, sem tabela temporária.
"""

import csv
import io

from django.core import signing
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from sgp.audit.services import record_event

from . import services
from .models import ImportMapping

SALT = "sgp.studies.import"
MAX_AGE = 60 * 60
UTF8_BOM = chr(0xFEFF)


def read_table(uploaded) -> tuple[list[str], list[list[str]]]:
    """Cabeçalho e linhas de um CSV (ponto e vírgula ou vírgula) ou do primeiro XLSX."""
    name = (uploaded.name or "").lower()
    data = uploaded.read()
    if name.endswith(".xlsx"):
        from openpyxl import load_workbook

        sheet = load_workbook(io.BytesIO(data), read_only=True, data_only=True).worksheets[0]
        table = [
            ["" if cell is None else str(cell) for cell in row]
            for row in sheet.iter_rows(values_only=True)
        ]
    elif name.endswith(".csv"):
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValidationError("O CSV precisa estar em UTF-8.") from exc
        text = text.lstrip(UTF8_BOM)
        first = text.splitlines()[0] if text else ""
        delimiter = ";" if first.count(";") >= first.count(",") else ","
        table = [row for row in csv.reader(io.StringIO(text), delimiter=delimiter)]
    else:
        raise ValidationError("Envie um arquivo CSV ou XLSX.")
    table = [row for row in table if any(str(cell).strip() for cell in row)]
    if not table:
        raise ValidationError("O arquivo está vazio.")
    return [str(h).strip() for h in table[0]], table[1:]


def apply_mapping(headers, rows, mapping: dict) -> list[dict]:
    index = {header: position for position, header in enumerate(headers)}
    missing = [column for column in mapping.values() if column and column not in index]
    if missing:
        raise ValidationError(f"Colunas não encontradas no arquivo: {', '.join(missing)}.")
    out = []
    for row in rows:
        out.append(
            {
                field: (row[index[column]] if index[column] < len(row) else "")
                for field, column in mapping.items()
                if column
            }
        )
    return out


def preview(study, uploaded, mapping: dict) -> dict:
    headers, rows = read_table(uploaded)
    raw = apply_mapping(headers, rows, mapping)
    valid, errors = services.normalize_rows(study, raw)
    payload = signing.dumps({"study": study.pk, "rows": _accepted(raw, errors)}, salt=SALT)
    return {
        "headers": headers,
        "total": len(raw),
        "valid": valid,
        "errors": errors,
        "token": payload,
        "accepted": len(raw) - len(errors),
    }


def _accepted(raw, errors) -> list[dict]:
    bad = {int(message.split(":")[0].replace("Linha ", "")) for message in errors}
    return [row for line, row in enumerate(raw, start=1) if line not in bad]


def confirm(study, *, by, token: str, equipment: str, mapping: dict, origin=None) -> int:
    """Grava as linhas aceitas; `origin` identifica a entrada do caderno promovida (feature 008)."""
    try:
        payload = signing.loads(token, salt=SALT, max_age=MAX_AGE)
    except signing.BadSignature as exc:
        raise ValidationError("A pré-visualização expirou; envie o arquivo de novo.") from exc
    if payload["study"] != study.pk:
        raise ValidationError("A pré-visualização é de outro estudo.")
    existing = [_raw(row) for row in study.rows]
    with transaction.atomic():
        study = services.save_rows(study, by=by, raw_rows=existing + payload["rows"])
        equipment = (equipment or "").strip()
        if equipment:
            ImportMapping.objects.update_or_create(
                equipment=equipment,
                defaults={"mapping": mapping, "updated_by": by, "updated_at": timezone.now()},
            )
            record_event(
                "studies.mapping_saved",
                actor=by,
                object_type="studies.importmapping",
                object_id=equipment[:64],
                object_repr=equipment[:255],
                new_value={"equipamento": equipment, "mapeamento": mapping},
            )
        record_event(
            "studies.imported",
            actor=by,
            obj=study,
            project_id=study.project_id,
            new_value={
                "linhas_importadas": len(payload["rows"]),
                "equipamento": equipment,
                **({"origem_caderno": origin} if origin else {}),
            },
        )
    return len(payload["rows"])


def _raw(row: dict) -> dict:
    """Linha gravada de volta ao formato de entrada (códigos dos cadastros)."""
    return {
        key: (value["codigo"] if isinstance(value, dict) else value) for key, value in row.items()
    }
