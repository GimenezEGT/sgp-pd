"""Tipos de campo: leitura, validação, vazio, resumo, referências e totais (FR-002 da feature 004)."""

from decimal import Decimal

import pytest
from django.http import QueryDict

from sgp.accounts.profiles import Profile
from sgp.catalog import versioning
from sgp.formtemplates import fieldtypes
from sgp.formtemplates.fieldtypes import Context

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("vocab_seed")]


def post(**values):
    data = QueryDict(mutable=True)
    for key, value in values.items():
        if isinstance(value, list):
            data.setlist(key, value)
        else:
            data[key] = value
    return data


@pytest.mark.req("004:FR-002")
@pytest.mark.parametrize(
    "text,expected",
    [
        ("12,5", Decimal("12.5")),
        ("1.234,56", Decimal("1234.56")),
        ("1234", Decimal("1234")),
        ("-3", Decimal("-3")),
    ],
)
def test_numero_no_padrao_brasileiro(text, expected):
    assert fieldtypes.parse_number(text) == expected


@pytest.mark.req("004:FR-002")
@pytest.mark.parametrize("text", ["1.5", "12.34.5", "abc", "1,2,3"])
def test_numero_ambiguo_ou_invalido_e_recusado(text):
    with pytest.raises(ValueError, match="vírgula"):
        fieldtypes.parse_number(text)


@pytest.mark.req("004:FR-002")
def test_tabela_le_numero_data_e_codigo_de_insumo(make_user):
    from tests.catalog.conftest import make_material  # noqa: F401

    editor = make_user(None, Profile.QUALITY)
    from sgp.catalog.kinds import MATERIALS

    material = versioning.create_record(
        MATERIALS,
        by=editor,
        data={"code": "MP-77", "description": "Tampão", "material_type": "raw"},
    )
    field_def = {
        "key": "itens",
        "type": "table",
        "label": "Itens",
        "columns": [
            {"key": "insumo", "label": "Insumo", "type": "reference", "kind": "insumos"},
            {"key": "qtd", "label": "Quantidade", "type": "number"},
            {"key": "data", "label": "Data", "type": "date"},
        ],
    }
    data = post(
        **{
            "p__0__insumo": "MP-77",
            "p__0__qtd": "1.250,5",
            "p__0__data": "2026-10-01",
            "p__1__insumo": "",
            "p__1__qtd": "",
            "p__1__data": "",
            "p__1700000000__insumo": "NAO-EXISTE",
            "p__1700000000__qtd": "1",
            "p__1700000000__data": "",
        }
    )
    value, errors = fieldtypes.parse(field_def, data, "p", Context())
    assert value[0] == {
        "insumo": {"id": material.pk, "code": "MP-77"},
        "qtd": "1250.5",
        "data": "2026-10-01",
    }
    assert len(value) == 2
    assert errors == [
        "Itens, linha 2, Insumo: Insumo NAO-EXISTE não encontrado entre os cadastros ativos."
    ]
    assert fieldtypes.references(field_def, value) == [("insumos", material.pk)]
    assert fieldtypes.summary(field_def, value[:1]).startswith("1 linha(s): MP-77")


@pytest.mark.req("004:FR-002")
def test_lista_controlada_aceita_inativo_so_se_ja_usado():
    from sgp.vocab.models import Term

    Term.objects.filter(vocabulary__code="automacao", code="outros").update(is_active=False)
    field_def = {
        "key": "tipo",
        "type": "vocabulary",
        "vocabulary": "automacao",
        "label": "Automação",
    }
    assert fieldtypes.validate(field_def, "manual", Context()) == []
    assert fieldtypes.validate(field_def, "outros", Context()) == [
        "Automação: opção inválida 'outros'."
    ]
    assert fieldtypes.validate(field_def, "outros", Context(previous="outros")) == []
    assert fieldtypes.summary(field_def, "manual") == "Manual"


@pytest.mark.req("004:FR-013")
def test_referencia_so_a_cadastros_disponiveis_e_do_projeto(make_user, open_project, make_lot):
    quality = make_user(None, Profile.QUALITY)
    project, other = open_project(), open_project()
    lot = make_lot(project, quality, code="LP-1")
    foreign = make_lot(other, quality, code="LP-2")
    field_def = {
        "key": "lotes",
        "type": "reference",
        "kind": "lotes",
        "label": "Lotes",
        "multiple": True,
    }
    ctx = Context(project=project)
    assert fieldtypes.validate(field_def, [lot.pk], ctx) == []
    assert fieldtypes.validate(field_def, [foreign.pk], ctx) == [
        f"Lotes: cadastro {foreign.pk} não pode ser escolhido aqui."
    ]
    versioning.set_active(lot, by=quality, active=False, reason="Descartado")
    assert fieldtypes.validate(field_def, [lot.pk], ctx)
    assert (
        fieldtypes.validate(field_def, [lot.pk], Context(project=project, previous=[lot.pk])) == []
    )


@pytest.mark.req("004:FR-002")
def test_aplica_nao_se_aplica():
    field_def = {
        "key": "requisitos",
        "type": "applicability",
        "label": "Requisitos",
        "vocabulary": "requisito-desempenho",
        "required": True,
    }
    rows = [
        {"codigo": "exatidao", "aplica": "sim", "criterio": "Bias < 5%", "justificativa": ""},
        {"codigo": "precisao", "aplica": "nao", "criterio": "", "justificativa": ""},
        {"codigo": "linearidade", "aplica": "", "criterio": "", "justificativa": ""},
    ]
    errors = fieldtypes.validate(field_def, rows, Context())
    assert errors == ["Requisitos: requisito Precisão marcado 'não se aplica' exige justificativa."]
    missing = fieldtypes.incomplete(field_def, rows)
    assert "Requisitos: marque 'aplica' ou 'não se aplica' em Linearidade." in missing
    assert fieldtypes.summary(field_def, rows) == "Aplica: Exatidão; Não se aplica: Precisão"


@pytest.mark.req("004:FR-019")
def test_derivada_exige_justificativa_fora_de_aprovado():
    field_def = {
        "key": "req",
        "type": "derived_table",
        "label": "Checklist",
        "source": "entry_topics",
        "rows": ["amostras"],
        "columns": [
            {
                "key": "disposicao",
                "label": "Disposição",
                "type": "vocabulary",
                "vocabulary": "disposicao",
            },
            {"key": "justificativa", "label": "Justificativa", "type": "text"},
        ],
        "justify_unless": {
            "column": "disposicao",
            "value": "aprovado",
            "justification": "justificativa",
        },
    }
    value = {
        "rows": [{"ref": "amostras", "label": "Amostras", "values": {"disposicao": "reprovado"}}]
    }
    assert (
        "disposição diferente de Aprovado exige justificativa"
        in fieldtypes.validate(field_def, value, Context())[0]
    )
    value["rows"][0]["values"]["justificativa"] = "Amostra de plasma não testada"
    assert fieldtypes.validate(field_def, value, Context()) == []


@pytest.mark.req("004:FR-011")
def test_total_e_vazio():
    field_def = {
        "key": "custos",
        "type": "table",
        "label": "Custos",
        "columns": [
            {"key": "item", "label": "Item", "type": "text"},
            {"key": "valor", "label": "Valor", "type": "number", "sum": True, "decimals": 2},
        ],
    }
    rows = [{"item": "Insumos", "valor": "1234.5"}, {"item": "Embalagem", "valor": "10"}]
    assert fieldtypes.column_total(field_def, rows, "valor") == "1.244,50"
    assert fieldtypes.has_table(field_def, rows) and not fieldtypes.has_table(field_def, [])
    assert fieldtypes.is_empty({"type": "rich_text"}, "") and not fieldtypes.is_empty(
        {"type": "list"}, ["a"]
    )


@pytest.mark.req("004:FR-002")
def test_data_texto_e_lista():
    assert fieldtypes.parse(
        {"key": "d", "type": "date", "label": "Data"}, post(d="07/11/2026"), "d", Context()
    ) == ("2026-11-07", [])
    value, errors = fieldtypes.parse(
        {"key": "d", "type": "date", "label": "Data"}, post(d="31/02/2026"), "d", Context()
    )
    assert errors == ["Data: Data inválida (use dd/mm/aaaa)."]
    assert fieldtypes.parse(
        {"key": "l", "type": "list", "label": "L"}, post(l="a\n\n b \n"), "l", Context()
    ) == (["a", "b"], [])
    assert fieldtypes.display_date("2026-11-07") == "07/11/2026"
