"""JSON Schema próprio e regras semânticas dos modelos (FR-001 a FR-003 da feature 004)."""

import copy

import pytest

from sgp.formtemplates import schema, seed_v05

ENTRY_KEYS = [topic["key"] for topic in seed_v05.ENTRADA["topics"]]


def minimal():
    return {
        "cover": {"title": "Modelo de teste", "columns": 1},
        "topics": [
            {"key": "um", "label": "Primeiro", "fields": [{"key": "texto", "type": "rich_text"}]},
            {"key": "dois", "label": "Segundo", "fields": [{"key": "lista", "type": "list"}]},
        ],
    }


@pytest.mark.req("004:FR-001")
@pytest.mark.req("004:FR-006")
@pytest.mark.parametrize("code", sorted(seed_v05.DEFINITIONS))
def test_definicoes_versao_05_sao_validas(code):
    assert schema.validate_definition(seed_v05.DEFINITIONS[code], entry_topic_keys=ENTRY_KEYS) == []


@pytest.mark.req("004:FR-002")
def test_tipo_de_campo_desconhecido_e_recusado():
    definition = minimal()
    definition["topics"][0]["fields"][0]["type"] = "planilha"
    errors = schema.validate_definition(definition)
    assert errors and errors[0].startswith("tópico 1 (Primeiro) › campo 1 (texto)")


@pytest.mark.req("004:FR-001")
@pytest.mark.parametrize("key", ["Maiuscula", "1numero", "com espaco", "a" * 41])
def test_chave_fora_do_padrao_e_recusada(key):
    definition = minimal()
    definition["topics"][0]["key"] = key
    assert schema.validate_definition(definition)


@pytest.mark.req("004:FR-003")
def test_rotulo_repetido_sem_diferenca_de_caixa_e_recusado():
    definition = minimal()
    definition["topics"][1]["label"] = "  primeiro "
    errors = schema.validate_definition(definition)
    assert any("rótulo repetido" in error for error in errors)


@pytest.mark.req("004:FR-003")
def test_chaves_repetidas_sao_recusadas():
    definition = minimal()
    definition["topics"][1]["key"] = "um"
    definition["topics"][0]["fields"].append({"key": "texto", "type": "text"})
    errors = schema.validate_definition(definition)
    assert any("chave 'um' repetida" in error for error in errors)
    assert any("campo 'texto' repetido" in error for error in errors)


@pytest.mark.req("004:FR-002")
def test_tabela_sem_colunas_e_lista_inexistente():
    definition = minimal()
    definition["topics"][0]["fields"] = [{"key": "tab", "type": "table"}]
    assert any("columns" in error for error in schema.validate_definition(definition))
    definition["topics"][0]["fields"] = [
        {"key": "sel", "type": "vocabulary", "vocabulary": "inexistente"}
    ]
    errors = schema.validate_definition(definition, vocabularies={"tipo-amostra"})
    assert any("lista controlada 'inexistente' não existe" in error for error in errors)


@pytest.mark.req("004:FR-002")
def test_linhas_derivadas_precisam_de_topicos_da_entrada():
    definition = copy.deepcopy(seed_v05.VERIFICACAO_FINAL)
    definition["topics"][0]["fields"][0]["rows"].append("topico_que_nao_existe")
    errors = schema.validate_definition(definition, entry_topic_keys=ENTRY_KEYS)
    assert any("topico_que_nao_existe" in error for error in errors)


@pytest.mark.req("004:FR-011")
def test_numeracao_pela_ordem_entre_os_visiveis():
    numbered = schema.numbered_topics(seed_v05.ENTRADA)
    numbers = [number for number, _ in numbered]
    assert numbers[:13] == list(range(1, 14)) and numbers[13] is None
    exit_anvisa = schema.numbered_topics(seed_v05.SAIDA, "ANVISA")
    assert [number for number, _ in exit_anvisa] == list(range(1, 11))
    exit_mapa = schema.numbered_topics(seed_v05.SAIDA, "MAPA")
    assert [number for number, _ in exit_mapa] == list(range(1, 13))


@pytest.mark.req("004:FR-001")
def test_definicao_que_nao_e_objeto():
    assert schema.validate_definition([]) == [
        "A definição precisa ser um objeto JSON com 'cover' e 'topics'."
    ]
