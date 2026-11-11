"""Definição do modelo de layout (FR-019, FR-022; contrato modelo-layout.md)."""

import copy

import pytest

from sgp.documents import layout_schema

CODES = ["entrada", "saida", "verificacao-final", "rapd", "analise-critica", "validacao"]


def _validate(definition, target="subdocument"):
    return layout_schema.validate_definition(definition, target=target, type_codes=CODES)


@pytest.mark.req("006:FR-022")
@pytest.mark.parametrize("target", ["subdocument", "charter", "business_plan"])
def test_padroes_da_versao_01_sao_validos(target):
    definition = layout_schema.default_definition(target)
    assert _validate(definition, target) == []
    assert (
        definition["page"]["margin_left_cm"] == 1.3 and definition["page"]["margin_top_cm"] == 2.0
    )
    assert definition["font"]["family"] == "Calibri"
    assert definition["watermark"]["text"] == "RASCUNHO " + chr(0x2013) + " NÃO VÁLIDO"


@pytest.mark.req("006:FR-022")
def test_padrao_de_subdocumentos_traz_as_particularidades_da_planilha():
    cover = layout_schema.default_definition("subdocument")["cover"]
    assert cover["title_pt"] == 24 and cover["title_pt_by_type"]["saida"] == 23
    assert cover["variant_by_type"] == {"verificacao-final": "checklist", "saida": "sectors"}
    assert cover["topics_pt"] == 14 and cover["topics_pt_by_type"] == {"saida": 11}


@pytest.mark.req("006:FR-019")
@pytest.mark.parametrize(
    ("section", "key", "value", "message"),
    [
        ("page", "margin_left_cm", 0.1, "valor fora do limite"),
        ("cover", "title_pt", 80, "valor fora do limite"),
        ("body", "table_header_fill", "cinza", "#RRGGBB"),
        ("font", "family", "Comic Sans", "valor não permitido"),
        ("watermark", "text", "", "preencha o texto"),
    ],
)
def test_valores_invalidos_sao_recusados_com_o_campo(section, key, value, message):
    definition = layout_schema.default_definition("subdocument")
    definition[section][key] = value
    errors = _validate(definition)
    assert errors and message in errors[0]


@pytest.mark.req("006:FR-019")
def test_campo_desconhecido_e_secao_faltando_sao_recusados():
    definition = layout_schema.default_definition("subdocument")
    broken = copy.deepcopy(definition)
    broken["page"]["extra"] = 1
    assert "campo desconhecido" in _validate(broken)[0]
    del definition["footer"]
    assert "falta rodapé" in _validate(definition)[0]
    assert layout_schema.schema_errors([]) != []


@pytest.mark.req("006:FR-019")
def test_marcador_desconhecido_no_cabecalho_e_recusado():
    definition = layout_schema.default_definition("subdocument")
    definition["header"]["text"] = "{titulo} {cliente}"
    errors = _validate(definition)
    assert errors and "{cliente}" in errors[0] and "{titulo}" in errors[0]


@pytest.mark.req("006:FR-022")
def test_tipo_inexistente_e_tamanho_por_tipo_fora_dos_subdocumentos_sao_recusados():
    definition = layout_schema.default_definition("subdocument")
    definition["cover"]["variant_by_type"]["inexistente"] = "topics"
    assert "inexistente" in _validate(definition)[0]
    charter = layout_schema.default_definition("charter")
    charter["cover"]["title_pt_by_type"] = {"entrada": 20}
    assert "só no layout de subdocumentos" in _validate(charter, "charter")[0]


@pytest.mark.req("006:FR-019")
def test_marcadores_sao_preenchidos_com_os_dados_do_documento():
    text = layout_schema.fill(
        "{titulo} – {produto} – Versão {versao} ({projeto}) {outro}",
        {"titulo": "Entrada de Projeto", "produto": "KIT", "versao": "01", "projeto": "PD-1"},
    )
    assert text == "Entrada de Projeto – KIT – Versão 01 (PD-1) {outro}"
