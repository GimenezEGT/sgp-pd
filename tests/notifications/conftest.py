"""Fixtures das notificações (feature 010). Dados fictícios criados só para os testes."""

import pytest

from tests.dashboard.conftest import submitted_entry  # noqa: F401
from tests.subdocuments.conftest import (  # noqa: F401
    analyst,
    make_subdocument,
    manager,
    project,
    standard,
)


@pytest.fixture
def emails(project, analyst, manager):
    for user, address in (
        (analyst, "analista@exemplo.test"),
        (manager, "gestor@exemplo.test"),
        (project.leader, "lider@exemplo.test"),
    ):
        user.email = address
        user.save(update_fields=["email"])
    return analyst, manager, project.leader
