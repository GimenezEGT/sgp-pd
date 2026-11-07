"""Comparação de instantâneos para a trilha: só os campos alterados, com valor anterior e novo."""


def changed_fields(before: dict, after: dict) -> tuple[dict, dict]:
    old, new = {}, {}
    for key in sorted(set(before) | set(after)):
        if before.get(key) != after.get(key):
            old[key] = before.get(key)
            new[key] = after.get(key)
    return old, new
