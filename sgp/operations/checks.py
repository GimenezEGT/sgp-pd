"""Execução comum dos itens de qualificação (research R8 da feature 014)."""

import logging
import socket
from collections.abc import Callable
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

APPROVED = "aprovado"
FAILED = "reprovado"
NOT_APPLICABLE = "nao_aplicavel"
RESULT_LABELS = {APPROVED: "Aprovado", FAILED: "Reprovado", NOT_APPLICABLE: "Não aplicável"}

Item = tuple[str, str, Callable[[], tuple[str, str]]]


def run_items(items: list[Item]) -> list[dict]:
    """Executa cada item; erro inesperado reprova o item com o motivo (nunca interrompe os demais)."""
    results = []
    for code, description, func in items:
        try:
            result, detail = func()
        except Exception as exc:  # noqa: BLE001 - o item reprova com o motivo
            logger.exception("Falha ao conferir %s", code)
            result, detail = FAILED, f"Erro ao conferir: {exc.__class__.__name__}: {exc}"
        results.append(
            {"codigo": code, "descricao": description, "resultado": result, "detalhe": detail}
        )
    return results


def tcp_reachable(host: str, port: int, timeout: float = 3.0) -> tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, f"{host}:{port} acessível."
    except OSError as exc:
        return False, f"{host}:{port} inacessível ({exc.__class__.__name__})."


def uri_host_port(uri: str, default_port: int) -> tuple[str, int]:
    parsed = urlparse(uri)
    return parsed.hostname or "", parsed.port or default_port


def worker_ping(timeout: float = 3.0) -> list[str]:
    """Nomes dos workers do Celery que responderam (vazio se nenhum)."""
    from config.celery import app

    replies = app.control.ping(timeout=timeout) or []
    return sorted(name for reply in replies for name in reply)
