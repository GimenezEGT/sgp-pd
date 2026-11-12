"""Fixtures da revisão controlada de modelos (feature 013). Dados fictícios só para os testes."""

import pytest

from tests.documents.conftest import generate, quality, seal_cert  # noqa: F401
from tests.subdocuments.conftest import (  # noqa: F401
    analyst,
    approve_quick,
    approved_entry,
    make_subdocument,
    manager,
    project,
    standard,
)


@pytest.fixture
def rapd_type(vocab_seed):
    from sgp.vocab.models import get_term

    return get_term("tipo-subdocumento", "rapd")


@pytest.fixture
def approver(make_user, signing):
    from sgp.accounts.profiles import Profile

    return signing.enable(make_user("gestor.modelos", Profile.RD_MANAGER))


@pytest.fixture
def form_draft(quality, rapd_type):
    """Rascunho da versão 06 da RAPD com o rótulo do primeiro tópico alterado."""
    from sgp.formtemplates import services

    draft = services.create_draft(rapd_type, by=quality)
    definition = dict(draft.definition)
    definition["topics"] = [dict(draft.topics[0], label="Formulações propostas (revisado)")]
    definition["topics"] += draft.topics[1:]
    return services.update_draft(draft, by=quality, data={}, definition=definition)


@pytest.fixture
def submitted(form_draft, quality):
    from sgp.revisions import services

    return services.submit(
        "form", form_draft, by=quality, reason="Ajuste de rótulo", impact="Só documentos novos"
    )
