"""Perfis de cálculo por tipo de estudo e critério atendido (FR-007, FR-009; perfis-calculo.md)."""

import pytest

from sgp.studies import profiles

CONFIG = {"rounding": "half_even", "places": 2, "fine_places": 4, "ci_method": "clopper_pearson"}


def g(results, name):
    return next(item for item in results["global"] if item["metrica"] == name)


@pytest.mark.req("007:FR-007")
def test_os_14_tipos_tem_perfil():
    assert len(profiles.PROFILES) == 14
    for profile in profiles.PROFILES.values():
        assert set(profile.criteria) <= set(profiles.LABELS)


@pytest.mark.req("007:FR-007")
def test_descritivo_por_dia_e_global():
    data = [{"dia": d, "y": y} for d, y in ((1, "10"), (1, "12"), (2, "11"), (2, "13"))]
    results = profiles.compute("reprodutibilidade", data, CONFIG)
    assert [group["rotulo"] for group in results["grupos"]] == ["Dia 1", "Dia 2"]
    assert g(results, "media")["arredondado"] == "11.50"
    assert g(results, "cv")["regra"] == "meio para o par, 2 casas"


@pytest.mark.req("007:FR-007")
def test_comparacao_de_metodos_e_regressao_com_4_casas():
    data = [{"x": x, "y": y} for x, y in (("1", "3"), ("2", "5"), ("3", "7"), ("4", "9"))]
    results = profiles.compute("comparacao-metodos", data, CONFIG)
    assert g(results, "diferenca_media")["arredondado"] == "3.50"
    assert (
        g(results, "r2")["arredondado"] == "1.0000"
        and g(results, "inclinacao")["arredondado"] == "2.0000"
    )


@pytest.mark.req("007:FR-007")
def test_sensibilidade_e_especificidade_com_ic():
    data = [{"esperado": "pos", "obtido": "pos"}] * 45 + [{"esperado": "pos", "obtido": "neg"}] * 5
    data += [{"esperado": "neg", "obtido": "neg"}] * 20
    results = profiles.compute("sensibilidade-especificidade", data, CONFIG)
    sens = g(results, "sensibilidade")
    assert sens["arredondado"] == "90.00" and sens["ic"] == ["78.19", "96.67"]
    assert g(results, "especificidade")["ic"] == ["83.16", "100.00"]
    wilson = profiles.compute(
        "sensibilidade-especificidade", data, {**CONFIG, "ci_method": "wilson"}
    )
    assert g(wilson, "sensibilidade")["ic"] == ["78.64", "95.65"]


@pytest.mark.req("007:FR-007")
def test_cut_off_com_interpretacao_menor_ou_igual():
    data = [
        {"y": "28", "esperado": "pos"},
        {"y": "36", "esperado": "neg"},
        {"y": "34", "esperado": "pos"},
    ]
    config = {**CONFIG, "cutoff": "35", "cutoff_direction": "le"}
    results = profiles.compute("cut-off", data, config)
    assert g(results, "concordancia")["arredondado"] == "100.00"
    without = profiles.compute("cut-off", data, CONFIG)
    assert g(without, "sensibilidade")["valor"] is None


@pytest.mark.req("007:FR-007")
def test_deteccao_interferentes_e_estabilidade():
    detection = profiles.compute(
        "sensibilidade-analitica",
        [
            {"grupo": "A", "x": "10", "obtido": "pos"},
            {"grupo": "A", "x": "10", "obtido": "pos"},
            {"grupo": "B", "x": "5", "obtido": "pos"},
            {"grupo": "B", "x": "5", "obtido": "neg"},
        ],
        CONFIG,
    )
    assert g(detection, "menor_nivel_detectado")["arredondado"] == "10.00"
    interference = profiles.compute(
        "interferentes",
        [
            {"grupo": "Hemoglobina", "x": "100", "y": "104"},
            {"grupo": "Bilirrubina", "x": "100", "y": "93"},
        ],
        CONFIG,
    )
    assert g(interference, "desvio_max")["arredondado"] == "7.00"
    stability = profiles.compute(
        "estabilidade-aberto",
        [{"x": "0", "y": "100"}, {"x": "30", "y": "95"}, {"x": "60", "y": "90"}],
        CONFIG,
    )
    assert g(stability, "variacao_max")["arredondado"] == "10.00"


@pytest.mark.req("007:FR-009")
@pytest.mark.req("007:FR-010")
def test_criterio_atendido_nao_atendido_e_nao_calculavel():
    results = profiles.compute(
        "repetibilidade", [{"y": v} for v in (2, 4, 4, 4, 5, 5, 7, 9)], CONFIG
    )
    evaluated = profiles.evaluate(
        [
            {"metrica": "cv", "comparacao": "lt", "limite": "15"},
            {"metrica": "media", "comparacao": "ge", "limite": "5"},
        ],
        results,
    )
    assert [(c["valor"], c["atendido"]) for c in evaluated] == [("42.76", False), ("5.00", True)]
    zero = profiles.compute("repetibilidade", [{"y": "0"}, {"y": "0"}], CONFIG)
    criterion = profiles.evaluate([{"metrica": "cv", "comparacao": "lt", "limite": "15"}], zero)[0]
    assert criterion["calculavel"] is False and criterion["atendido"] is False
