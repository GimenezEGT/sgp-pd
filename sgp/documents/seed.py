"""Versão 01 publicada dos modelos de layout (padrões da prova de layout; research R10 e R14)."""

from .layout_schema import default_definition

TARGETS = ("subdocument", "charter", "business_plan")
NOTE = "Versão inicial: padrões da planilha Capas Projeto (prova de layout da feature 006)."


def load(apps, *, valid_from, published_at) -> None:
    """Idempotente: cria a versão 01 publicada de cada alvo que ainda não tem nenhuma versão."""
    layout_model = apps.get_model("documents", "LayoutTemplate")
    for target in TARGETS:
        if layout_model.objects.filter(target=target).exists():
            continue
        layout_model.objects.create(
            target=target,
            version=1,
            valid_from=valid_from,
            status="published",
            definition=default_definition(target),
            note=NOTE,
            created_at=published_at,
            published_at=published_at,
        )
