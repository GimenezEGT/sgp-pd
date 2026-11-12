"""Mapeamento configurável dos registros para o Sankhya (research R3 da feature 012)."""

from pathlib import Path

import yaml
from django.core.exceptions import ValidationError

DEFAULT_PATH = Path(__file__).with_name("mapeamento_padrao.yaml")
RECORD_FIELDS = {
    "projeto": (
        "codigo_projeto",
        "nome",
        "produto",
        "tecnologia",
        "orgao",
        "classe_risco",
        "lider",
        "situacao",
        "versao_projeto",
        "data_abertura",
    ),
    "documento": (
        "codigo_projeto",
        "tipo_subdocumento",
        "versao_documento",
        "versao_formulario",
        "referencia_psg",
        "data_aprovacao",
        "elaborador",
        "aprovador",
        "resumo_conteudo",
        "pdf_sha256",
        "pdf_codigo_verificacao",
    ),
    "lote": (
        "codigo_lote",
        "tipo",
        "codigo_projeto",
        "data_fabricacao",
        "data_validade",
        "local",
        "responsavel",
    ),
    "insumo_novo": (
        "descricao",
        "tipo",
        "fabricante",
        "lote_fabricante",
        "certificado_nome",
        "certificado_sha256",
        "codigo_projeto",
        "situacao",
    ),
    "resultado_estudo": (
        "codigo_projeto",
        "tipo_estudo",
        "titulo",
        "versao",
        "criterio",
        "resultado",
        "conclusao",
        "documento_origem",
    ),
}
PRODUCT_FIELDS = ("codigo", "descricao", "unidade", "situacao")
RECORD_LABELS = {
    "projeto": "Projeto P&D",
    "documento": "Documento P&D",
    "lote": "Lote P&D",
    "insumo_novo": "Insumo novo",
    "resultado_estudo": "Resultado de estudo",
}


def default_yaml() -> str:
    return DEFAULT_PATH.read_text(encoding="utf-8")


def _text(value) -> str:
    return "" if value is None else str(value).strip()


def parse(text: str) -> dict:
    """YAML → mapeamento normalizado; campos lógicos desconhecidos e entidade sem chave são recusados."""
    try:
        data = yaml.safe_load(text or "")
    except yaml.YAMLError as exc:
        raise ValidationError(f"YAML inválido: {exc}") from exc
    if not isinstance(data, dict):
        raise ValidationError("O mapeamento precisa ser um mapa com 'produto' e 'registros'.")
    errors = []
    product = data.get("produto") or {}
    product_fields = {name: _text(value) for name, value in (product.get("campos") or {}).items()}
    unknown = set(product_fields) - set(PRODUCT_FIELDS)
    if unknown:
        errors.append(f"produto: campos desconhecidos {', '.join(sorted(unknown))}.")
    if _text(product.get("entidade")) and not (
        product_fields.get("codigo") and product_fields.get("descricao")
    ):
        errors.append("produto: com entidade informada, mapeie ao menos código e descrição.")
    records = {}
    raw_records = data.get("registros") or {}
    for record_type, fields in RECORD_FIELDS.items():
        raw = raw_records.get(record_type) or {}
        mapped = {name: _text(value) for name, value in (raw.get("campos") or {}).items()}
        unknown = set(mapped) - set(fields)
        if unknown:
            errors.append(f"{record_type}: campos desconhecidos {', '.join(sorted(unknown))}.")
        entity, key = _text(raw.get("entidade")), _text(raw.get("chave"))
        if entity and not key:
            errors.append(f"{record_type}: com entidade informada, a 'chave' é obrigatória.")
        records[record_type] = {"entidade": entity, "chave": key, "campos": mapped}
    unknown_records = set(raw_records) - set(RECORD_FIELDS)
    if unknown_records:
        errors.append(f"Registros desconhecidos: {', '.join(sorted(unknown_records))}.")
    if errors:
        raise ValidationError(errors)
    return {
        "formato": data.get("formato", 1),
        "produto": {"entidade": _text(product.get("entidade")), "campos": product_fields},
        "registros": records,
    }
