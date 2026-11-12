"""Versão do sistema nas evidências: manifesto, registros e relatórios (research R9 da 014)."""

import tomllib
from functools import lru_cache
from pathlib import Path

from django.conf import settings


@lru_cache(maxsize=1)
def project_version() -> str:
    try:
        data = tomllib.loads((Path(settings.BASE_DIR) / "pyproject.toml").read_text("utf-8"))
    except (OSError, ValueError):
        return ""
    return str((data.get("project") or {}).get("version") or "")


def _git_commit() -> str:
    """Commit do repositório montado (desenvolvimento); a imagem de produção usa SGP_COMMIT."""
    git = Path(settings.BASE_DIR) / ".git"
    try:
        head = (git / "HEAD").read_text("utf-8").strip()
        if not head.startswith("ref: "):
            return head[:40]
        ref = head[5:]
        if (git / ref).is_file():
            return (git / ref).read_text("utf-8").strip()[:40]
        for line in (git / "packed-refs").read_text("utf-8").splitlines():
            if line.endswith(" " + ref):
                return line.split(" ", 1)[0][:40]
    except OSError:
        return ""
    return ""


def commit() -> str:
    return (getattr(settings, "SGP_COMMIT", "") or "").strip() or _git_commit()


def current() -> dict:
    return {"versao": project_version(), "commit": commit()}


def display() -> str:
    info = current()
    text = info["versao"] or "sem versão"
    return f"{text} ({info['commit'][:12]})" if info["commit"] else text
