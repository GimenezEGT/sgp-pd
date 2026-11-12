"""Comparação por item entre versões do dossiê (FR-012; research R6)."""

import difflib


def changes(previous: dict, current: dict) -> list[dict]:
    """Itens cujo texto ou situação mudou, na ordem do dossiê atual."""
    out = []
    for key, item in current.items():
        before = previous.get(key, {"linhas": [], "status": ""})
        if before.get("linhas") == item.get("linhas") and before.get("status") == item.get(
            "status"
        ):
            continue
        out.append(
            {
                "key": key,
                "titulo": item["titulo"],
                "before": before.get("linhas", []),
                "after": item.get("linhas", []),
                "diff": list(
                    difflib.unified_diff(
                        before.get("linhas", []), item.get("linhas", []), lineterm="", n=1
                    )
                )[2:],
            }
        )
    for key, item in previous.items():
        if key not in current:
            out.append(
                {
                    "key": key,
                    "titulo": item["titulo"],
                    "before": item["linhas"],
                    "after": [],
                    "diff": [],
                }
            )
    return out
