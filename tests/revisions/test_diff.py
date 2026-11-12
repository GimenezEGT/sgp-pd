"""Comparação entre versões de modelo (FR-007, FR-018)."""

import pytest

from sgp.revisions import diff

BASE = {
    "cover": {"title": "RAPD", "columns": 1},
    "topics": [
        {"key": "a", "label": "Tópico A", "fields": [{"key": "x", "type": "text", "label": "X"}]},
        {"key": "b", "label": "Tópico B", "fields": []},
    ],
}


@pytest.mark.req("013:FR-018")
def test_inclusao_retirada_e_alteracao_por_chave():
    new = {
        "cover": {"title": "RAPD revisada", "columns": 1},
        "topics": [
            {
                "key": "a",
                "label": "Tópico A",
                "fields": [{"key": "x", "type": "text", "label": "X novo"}],
            },
            {
                "key": "c",
                "label": "Tópico C",
                "fields": [{"key": "y", "type": "text", "label": "Y"}],
            },
        ],
    }
    result = diff.compare(BASE, new)
    assert result["added"] == [("tópico «Tópico C»", "Tópico C")]
    assert result["removed"] == [("tópico «Tópico B»", "Tópico B")]
    changed = {label: (before, after) for label, before, after in result["changed"]}
    assert changed["capa › título"] == ("RAPD", "RAPD revisada")
    assert changed["tópico «Tópico A» › campo «X novo» › rótulo"] == ("X", "X novo")


@pytest.mark.req("013:FR-007")
def test_definicao_igual_nao_tem_mudanca():
    assert diff.is_empty(diff.compare(BASE, dict(BASE)))
    assert not diff.is_empty(diff.compare({}, BASE))


@pytest.mark.req("013:FR-018")
def test_reordenar_topicos_nao_e_mudanca_de_conteudo_mas_valor_de_lista_e():
    reordered = dict(BASE, topics=list(reversed(BASE["topics"])))
    assert diff.is_empty(diff.compare(BASE, reordered))
    assert not diff.is_empty(diff.compare({"rows": ["a", "b"]}, {"rows": ["b", "a"]}))
