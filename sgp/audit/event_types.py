"""Catálogo de tipos de evento da trilha. Cada app registra os seus códigos e rótulos."""

EVENT_TYPES: dict[str, str] = {}


def register(code: str, label: str) -> None:
    current = EVENT_TYPES.get(code)
    if current is not None and current != label:
        raise ValueError(f"Tipo de evento {code} já registrado com outro rótulo.")
    EVENT_TYPES[code] = label


def register_many(mapping: dict[str, str]) -> None:
    for code, label in mapping.items():
        register(code, label)


def label_for(code: str) -> str:
    return EVENT_TYPES.get(code, code)


def choices() -> list[tuple[str, str]]:
    return sorted(EVENT_TYPES.items(), key=lambda item: item[1])


register_many(
    {
        "audit.exported": "Trilha exportada",
        "audit.chain_verified": "Integridade da trilha verificada",
    }
)
