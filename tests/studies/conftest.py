"""Fixtures dos estudos (feature 007). Dados fictícios criados só para os testes."""

import pytest

from tests.catalog.conftest import lot_data, make_lot, make_material  # noqa: F401
from tests.documents.conftest import generate, seal_cert  # noqa: F401
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
def study_type(vocab_seed):
    from sgp.vocab.models import get_term

    def _type(code):
        return get_term("tipo-estudo", code)

    return _type


@pytest.fixture
def rapd(project, approved_entry, make_subdocument, approve_quick):
    for code in ("formulacao", "lote-piloto"):
        approve_quick(make_subdocument(project, code))
    return make_subdocument(project, "rapd")


@pytest.fixture
def make_study(project, analyst, study_type):
    from sgp.studies import services

    def _make(code="repetibilidade", by=None, **data):
        values = {"study_type": study_type(code), "title": f"Estudo de {code}"}
        values.update(data)
        return services.create_study(project, by=by or analyst, data=values)

    return _make


def rows(values, column="y", **extra):
    return [{column: str(value).replace(".", ","), **extra} for value in values]
