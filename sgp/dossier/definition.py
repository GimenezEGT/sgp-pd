"""Leitura e validação da definição declarativa do dossiê (research R1 da feature 011)."""

from pathlib import Path

import yaml
from django.core.exceptions import ValidationError

DEFAULT_PATH = Path(__file__).with_name("definicao_padrao.yaml")
SOURCE_TYPES = {
    "subdocumento",
    "estudos",
    "normas",
    "referencias",
    "anexos",
    "texto_padrao",
    "complemento",
}
CLASSES = ("I", "II", "III", "IV")


def default_yaml() -> str:
    return DEFAULT_PATH.read_text(encoding="utf-8")


def _check_source(source, where: str, errors: list[str]) -> None:
    if not isinstance(source, dict) or source.get("tipo") not in SOURCE_TYPES:
        errors.append(f"{where}: fonte sem tipo válido ({', '.join(sorted(SOURCE_TYPES))}).")
        return
    kind = source["tipo"]
    if kind in ("subdocumento", "anexos") and not (
        source.get("subdocumento") and source.get("topico")
    ):
        errors.append(f"{where}: a fonte '{kind}' precisa de subdocumento e tópico.")
    if kind == "estudos" and not source.get("tipos"):
        errors.append(f"{where}: a fonte 'estudos' precisa da lista de tipos.")
    if kind == "texto_padrao" and not source.get("chave"):
        errors.append(f"{where}: a fonte 'texto_padrao' precisa da chave do texto.")


def _walk(items, prefix: str, errors: list[str], seen: set) -> list[dict]:
    out = []
    if not isinstance(items, list) or not items:
        errors.append(f"{prefix or 'Dossiê'}: lista de itens vazia.")
        return out
    for item in items:
        if not isinstance(item, dict):
            errors.append(f"{prefix}: item inválido.")
            continue
        number = str(item.get("numero", "")).strip()
        title = str(item.get("titulo", "")).strip()
        key = f"{prefix}.{number}" if prefix else number
        if not number or not title:
            errors.append(f"{key or prefix}: todo item precisa de número e título.")
            continue
        if key in seen:
            errors.append(f"{key}: número repetido.")
        seen.add(key)
        classes = item.get("classes")
        if classes is not None:
            invalid = [c for c in classes if str(c) not in CLASSES]
            if invalid or not classes:
                errors.append(f"{key}: classes válidas são I, II, III e IV.")
            if not item.get("fora_da_classe"):
                errors.append(
                    f"{key}: item limitado por classe precisa da justificativa 'fora_da_classe'."
                )
        children = item.get("subitens")
        sources = item.get("fontes")
        node = {
            "key": key,
            "numero": number,
            "titulo": title,
            "classes": [str(c) for c in classes] if classes else None,
            "fora_da_classe": item.get("fora_da_classe", ""),
        }
        if children:
            if sources:
                errors.append(f"{key}: item com subitens não tem fontes próprias.")
            node["subitens"] = _walk(children, key, errors, seen)
        else:
            if not sources:
                errors.append(f"{key}: item final precisa de ao menos uma fonte.")
            for index, source in enumerate(sources or [], start=1):
                _check_source(source, f"{key} (fonte {index})", errors)
            node["fontes"] = sources or []
        out.append(node)
    return out


def parse(text: str) -> dict:
    """YAML → definição normalizada; erros de estrutura viram ValidationError com a lista."""
    try:
        data = yaml.safe_load(text or "")
    except yaml.YAMLError as exc:
        raise ValidationError(f"YAML inválido: {exc}") from exc
    if not isinstance(data, dict):
        raise ValidationError("A definição precisa ser um mapa com 'itens'.")
    errors: list[str] = []
    items = _walk(data.get("itens"), "", errors, set())
    if errors:
        raise ValidationError(errors)
    return {"formato": data.get("formato", 1), "itens": items}


def leaves(items, parents=()):
    """(item final, ancestrais) em ordem de leitura."""
    for item in items:
        if item.get("subitens"):
            yield from leaves(item["subitens"], (*parents, item))
        else:
            yield item, parents


def applies(item, parents, risk_class: str | None) -> tuple[bool, str]:
    """O item vale para a classe? (sim, "") ou (não, justificativa da definição)."""
    for node in (*parents, item):
        if node.get("classes") and risk_class not in node["classes"]:
            return False, node.get("fora_da_classe", "")
    return True, ""
