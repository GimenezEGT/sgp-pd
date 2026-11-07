"""Representação canônica do conteúdo assinado e seu SHA-256 (research R3 da feature 005).

Reaproveita a redução de valores da trilha de auditoria (sem ponto flutuante, datas ISO) e grava o
JSON com chaves ordenadas e separadores compactos, para que o mesmo conteúdo dê sempre o mesmo
resumo.
"""

import hashlib
import json

from sgp.audit.chain import to_jsonable


def canonical_json(content) -> str:
    return json.dumps(
        to_jsonable(content), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def content_hash(content) -> str:
    return hashlib.sha256(canonical_json(content).encode("utf-8")).hexdigest()


def normalized(content):
    """O conteúdo como fica guardado (o mesmo que entra no resumo)."""
    return json.loads(canonical_json(content))
