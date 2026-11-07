"""Mascaramento de campos sensíveis na trilha (feature 002, FR-010)."""

from types import SimpleNamespace

import pytest

from sgp.audit import masking

pytestmark = pytest.mark.req("002:FR-010")


def test_chaves_sensiveis_sao_mascaradas_em_qualquer_nivel():
    value = {
        "total_cost": "10.00",
        "outros": {"total_cost": "1", "nome": "x"},
        "lista": [{"total_cost": 2}],
    }
    assert masking.mask_value(value, frozenset({"total_cost"})) == {
        "total_cost": masking.MASK,
        "outros": {"total_cost": masking.MASK, "nome": "x"},
        "lista": [{"total_cost": masking.MASK}],
    }


def test_present_respeita_a_regra_registrada():
    masking.register(
        "teste.sensivel", {"segredo"}, lambda viewer, project_id, cache: viewer == "pode"
    )
    event = SimpleNamespace(
        event_type="teste.sensivel",
        project_id=1,
        old_value={"segredo": 1},
        new_value={"segredo": 2, "livre": 3},
    )
    assert masking.present(event, "pode") == ({"segredo": 1}, {"segredo": 2, "livre": 3})
    assert masking.present(event, "nao") == (
        {"segredo": masking.MASK},
        {"segredo": masking.MASK, "livre": 3},
    )


def test_evento_sem_regra_nao_e_alterado():
    event = SimpleNamespace(
        event_type="audit.exported", project_id=None, old_value=None, new_value={"a": 1}
    )
    assert masking.present(event, None) == (None, {"a": 1})
