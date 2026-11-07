"""Fixtures da assinatura (feature 005), sobre as dos subdocumentos e cadastros."""

import pytest

from tests.catalog.conftest import lot_data, make_lot, make_material  # noqa: F401
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
def complete_formulation(project, approved_entry, make_subdocument, analyst, make_material):
    """Elaboração de Formulação completa, em rascunho, pronta para enviar."""
    from sgp.subdocuments import services

    material = make_material(analyst, code="MP-ASS")
    formulation = make_subdocument(project, "formulacao")
    return services.save_subdocument(
        formulation,
        by=analyst,
        data={
            "topics": {
                "reagentes": {
                    "na": False,
                    "justification": "",
                    "values": {"reagentes": [{"numero": "R1", "nome": "Tampão", "composicao": ""}]},
                },
                "materias_primas": {
                    "na": False,
                    "justification": "",
                    "values": {
                        "itens": [
                            {"reagente": "R1", "insumo": {"id": material.pk, "code": "MP-ASS"}}
                        ]
                    },
                },
                "modo_preparo": {
                    "na": False,
                    "justification": "",
                    "values": {"componentes": [], "passos": "Dissolver"},
                },
                "complementares": {"na": True, "justification": "Não há", "values": {"texto": ""}},
            }
        },
    )
