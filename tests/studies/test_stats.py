"""Cálculos com os vetores de referência de docs/contexto/06-casos-de-teste.md (V1 a V8) e
propriedades (FR-007, FR-010 a FR-012, SC-001)."""

from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from sgp.studies import stats


def r(value, places=2, rule="half_even"):
    return str(stats.round_value(value, places, rule))


@pytest.mark.req("007:FR-012")
@pytest.mark.req("007:SC-001")
def test_v1_media_dp_e_cv():
    result = stats.describe([2, 4, 4, 4, 5, 5, 7, 9])
    assert result["media"] == 5
    assert r(result["dp"], 5) == "2.13809"
    assert result["dp_populacional"] == 2
    assert r(result["cv"]) == "42.76"


@pytest.mark.req("007:FR-012")
@pytest.mark.req("007:SC-001")
def test_v2_precisao_numerica_numacc1():
    result = stats.describe(["10000001", "10000003", "10000002"])
    assert result["media"] == Decimal("10000002") and result["dp"] == 1


@pytest.mark.req("007:FR-012")
@pytest.mark.req("007:SC-001")
def test_v3_regressao_exata():
    result = stats.regression([1, 2, 3, 4], [3, 5, 7, 9])
    assert (result["inclinacao"], result["intercepto"], result["r2"]) == (2, 1, 1)


@pytest.mark.req("007:FR-012")
@pytest.mark.req("007:SC-001")
def test_v4_regressao_com_ruido():
    result = stats.regression([1, 2, 3, 4, 5], ["1.1", "1.9", "3.2", "3.8", "5.1"])
    assert r(result["inclinacao"]) == "0.99" and r(result["intercepto"]) == "0.05"
    assert r(result["r2"], 4) == "0.9892"


@pytest.mark.req("007:FR-012")
@pytest.mark.req("007:SC-001")
@pytest.mark.parametrize(
    ("k", "n", "low", "high"),
    [
        (45, 50, "78.19", "96.67"),
        (18, 20, "68.30", "98.77"),
        (20, 20, "83.16", "100.00"),
        (0, 20, "0.00", "16.84"),
    ],
)
def test_v5_clopper_pearson(k, n, low, high):
    result = stats.proportion(k, n)
    assert (r(result["ic_inferior"]), r(result["ic_superior"])) == (low, high)


@pytest.mark.req("007:FR-012")
@pytest.mark.req("007:SC-001")
def test_v6_wilson():
    result = stats.proportion(45, 50, "wilson")
    assert (r(result["ic_inferior"]), r(result["ic_superior"])) == ("78.64", "95.65")


@pytest.mark.req("007:FR-011")
@pytest.mark.req("007:SC-001")
@pytest.mark.parametrize(
    ("rule", "expected"),
    [
        ("truncate", ["1.034", "0.124", "0.123"]),
        ("half_up", ["1.035", "0.125", "0.124"]),
        ("half_even", ["1.035", "0.124", "0.124"]),
    ],
)
def test_v7_arredondamento_em_3_casas(rule, expected):
    assert [r(v, 3, rule) for v in ("1.0349", "0.1245", "0.1235")] == expected


@pytest.mark.req("007:FR-011")
@pytest.mark.req("007:SC-001")
def test_v8_arredondamento_para_inteiro():
    assert [r("2.5", 0, rule) for rule in ("truncate", "half_up", "half_even")] == ["2", "3", "2"]


@pytest.mark.req("007:FR-010")
def test_nao_calculaveis():
    assert stats.describe([0, 0, 0])["cv"] is None
    single = stats.describe([7])
    assert single["dp"] is None and single["cv"] is None and single["media"] == 7
    assert stats.regression([2, 2, 2], [1, 2, 3])["r2"] is None
    assert stats.proportion(0, 0)["proporcao"] is None
    assert stats.percent_deviation(0, 5) is None


@pytest.mark.req("007:FR-007")
def test_diferencas_classificacao_e_contingencia():
    diffs = stats.differences([10, 20, 30], [11, 21, 33])
    assert diffs["diferenca_media"] == Decimal("5") / 3
    assert stats.classify("35", "30", "le") == "neg" and stats.classify("25", "30", "le") == "pos"
    table = stats.contingency([("pos", "pos"), ("pos", "neg"), ("neg", "neg"), ("neg", "pos")])
    assert table == {"vp": 1, "fn": 1, "vn": 1, "fp": 1}


values = st.lists(
    st.decimals(min_value=-1000, max_value=1000, places=3, allow_nan=False, allow_infinity=False),
    min_size=2,
    max_size=40,
)


@pytest.mark.req("007:FR-007")
@settings(max_examples=60, deadline=None)
@given(values, st.decimals(min_value=-100, max_value=100, places=2))
def test_propriedades_da_media_e_do_desvio(data, shift):
    result = stats.describe(data)
    assert min(data) <= result["media"] <= max(data)
    assert result["dp"] >= 0
    shifted = stats.describe([v + shift for v in data])
    assert abs(shifted["dp"] - result["dp"]) < Decimal("1e-20")


@pytest.mark.req("007:FR-011")
@settings(max_examples=60, deadline=None)
@given(st.decimals(min_value=-1000, max_value=1000, places=6), st.integers(0, 4))
def test_arredondar_duas_vezes_nao_muda(value, places):
    for rule in stats.RULES:
        once = stats.round_value(value, places, rule)
        assert stats.round_value(once, places, rule) == once


@pytest.mark.req("007:FR-007")
@settings(max_examples=40, deadline=None)
@given(st.integers(0, 60), st.integers(1, 60))
def test_ic_contem_a_proporcao_observada(k, extra):
    n = k + extra if extra else k
    for method in ("clopper_pearson", "wilson"):
        result = stats.proportion(k, n, method)
        assert (
            result["ic_inferior"] - Decimal("1e-9")
            <= result["proporcao"]
            <= result["ic_superior"] + Decimal("1e-9")
        )
