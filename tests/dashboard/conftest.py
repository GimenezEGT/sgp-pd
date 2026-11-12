"""Fixtures do painel (feature 010). Dados fictícios criados só para os testes."""

import pytest

from tests.subdocuments.conftest import (  # noqa: F401
    analyst,
    approve_quick,
    make_subdocument,
    manager,
    project,
    standard,
)


@pytest.fixture(autouse=True)
def clean_cache():
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def submitted_entry(project, analyst, make_subdocument, standard, signing):
    """Entrada completa enviada para revisão pela analista (assinatura "elaborado")."""
    from sgp.subdocuments import services
    from tests.subdocuments.conftest import entry_topics

    entry = make_subdocument(project, "entrada")
    entry = services.save_subdocument(entry, by=analyst, data={"topics": entry_topics(standard.pk)})
    signing.submit("subdocument", entry, analyst)
    entry.refresh_from_db()
    return entry
