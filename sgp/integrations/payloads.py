"""Corpo das chamadas ao gateway (research R2 da feature 012).

PROVISÓRIO: segue a estrutura pública da documentação da Sankhya ("Incluir e Alterar Dados" e
"Como consultar dados?"); o formato exato precisa ser confirmado com a consultoria antes da
homologação. Tudo o que depende desse formato está só neste módulo.
"""

LOAD = "CRUDServiceProvider.loadRecords"
SAVE = "CRUDServiceProvider.saveRecord"


def save_record(entity: str, key_field: str, key: str, fields: dict) -> dict:
    local = {key_field: {"$": key}}
    for name, value in fields.items():
        if name and name != key_field:
            local[name] = {"$": "" if value is None else str(value)}
    return {
        "serviceName": SAVE,
        "requestBody": {
            "dataSet": {
                "rootEntity": entity,
                "includePresentationFields": "N",
                "dataRow": {"localFields": local},
                "entity": {"fieldset": {"list": ",".join(local)}},
            }
        },
    }


def load_records(entity: str, fields: list[str], code_field: str, code: str) -> dict:
    return {
        "serviceName": LOAD,
        "requestBody": {
            "dataSet": {
                "rootEntity": entity,
                "includePresentationFields": "N",
                "offsetPage": "0",
                "criteria": {
                    "expression": {"$": f"this.{code_field} = ?"},
                    "parameter": [{"$": str(code), "type": "S"}],
                },
                "entity": {"fieldset": {"list": ",".join(fields)}},
            }
        },
    }


def rows(response: dict) -> list[dict]:
    """Linhas de `loadRecords`: nomes dos campos vêm dos metadados, valores em f0, f1…"""
    entities = (response.get("responseBody") or {}).get("entities") or {}
    meta = ((entities.get("metadata") or {}).get("fields") or {}).get("field") or []
    meta = meta if isinstance(meta, list) else [meta]
    names = [field.get("name") for field in meta]
    raw = entities.get("entity") or []
    raw = raw if isinstance(raw, list) else [raw]
    out = []
    for entity in raw:
        out.append(
            {name: (entity.get(f"f{index}") or {}).get("$", "") for index, name in enumerate(names)}
        )
    return out
