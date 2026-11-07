"""Carga inicial dos modelos versão 05 (FR-006, SC-001 da feature 004)."""

import pytest

from sgp.formtemplates import schema
from sgp.formtemplates.models import FormTemplate
from sgp.formtemplates.services import current_template, definition_errors
from sgp.vocab.models import Term, get_term

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("vocab_seed")]


@pytest.mark.req("004:FR-006")
@pytest.mark.req("004:SC-001")
def test_nove_modelos_versao_05_publicados_e_validos():
    templates = FormTemplate.objects.filter(form_version=5, status="published")
    codes = set(templates.values_list("subdocument_type__code", flat=True))
    assert codes == set(Term.objects.of("tipo-subdocumento").values_list("code", flat=True))
    for template in templates:
        assert definition_errors(template, template.definition) == []
        assert template.footer == (
            "Formulário Versão: 05. Referência: PSG 20 - Pesquisa e Desenvolvimento de Produtos"
        )


@pytest.mark.req("004:FR-006")
def test_entrada_tem_13_topicos_e_o_formulario_opcional():
    entry = current_template(get_term("tipo-subdocumento", "entrada"))
    numbered = schema.numbered_topics(entry.definition)
    cover = [topic["label"] for number, topic in numbered if number]
    assert len(cover) == 13
    assert cover[8] == "Classificação de Risco (RDC 830/2023)"
    assert cover[5] == "Classificação de uso"
    assert entry.topic("formulario_opcional")["in_cover"] is False
    assert entry.topic("apresentacoes")["body_label"] == "Apresentações e Composições"


@pytest.mark.req("004:FR-006")
def test_analise_critica_saida_e_verificacao_final():
    critical = current_template(get_term("tipo-subdocumento", "analise-critica"))
    assert len(critical.topics) == 3
    exit_doc = current_template(get_term("tipo-subdocumento", "saida"))
    assert len(exit_doc.topics) == 12
    assert [t["key"] for t in exit_doc.topics if t.get("regulatory_body") == "MAPA"] == [
        "lotes_piloto_producao",
        "testes_cq",
    ]
    final = current_template(get_term("tipo-subdocumento", "verificacao-final"))
    assert len(final.topics[0]["fields"][0]["rows"]) == 11
    validation = current_template(get_term("tipo-subdocumento", "validacao"))
    assert validation.cover["approver_label"] == "Gestor de P&D responsável pela Aprovação:"
