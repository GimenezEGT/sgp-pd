"""Dinheiro em formato brasileiro (FR-009 da feature 002)."""

from decimal import Decimal

import pytest
from django import forms

from sgp.core.formatting import format_brl, format_int_br
from sgp.projects.fields import BRLMoneyField, LinesField, parse_brl

pytestmark = pytest.mark.req("002:FR-009")


@pytest.mark.parametrize(
    "text,expected",
    [
        ("1.234.567,89", Decimal("1234567.89")),
        ("1234567,89", Decimal("1234567.89")),
        ("R$ 1.234,00", Decimal("1234.00")),
        ("1234.56", Decimal("1234.56")),
        ("1.234", Decimal("1234")),
        ("0,5", Decimal("0.5")),
        ("", None),
    ],
)
def test_parse_brl(text, expected):
    assert parse_brl(text) == expected


def test_campo_normaliza_para_duas_casas():
    assert BRLMoneyField().clean("1.000") == Decimal("1000.00")


@pytest.mark.parametrize(
    "text,message",
    [
        ("-10,00", "não pode ser negativo"),
        ("10,123", "no máximo 2 casas"),
        ("abc", "Informe um valor em reais"),
        ("1.000.000.000.000,00", "acima do limite"),
    ],
)
def test_campo_recusa_valores_invalidos(text, message):
    with pytest.raises(forms.ValidationError, match=message):
        BRLMoneyField().clean(text)


def test_exibicao_no_padrao_brasileiro():
    assert format_brl(Decimal("1234567.891")) == "R$ 1.234.567,89"
    assert format_brl(Decimal("0")) == "R$ 0,00"
    assert format_brl(None) == ""
    assert format_int_br(120000) == "120.000"
    assert BRLMoneyField().prepare_value(Decimal("1234.5")) == "1.234,50"


def test_campo_de_linhas():
    field = LinesField()
    assert field.clean("A\n\n B \nC") == ["A", "B", "C"]
    assert field.prepare_value(["A", "B"]) == "A\nB"
