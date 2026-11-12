"""Conteúdo de renderização dos subdocumentos (FR-001, FR-004 a FR-010; conteudo-renderizacao.md)."""

import pytest

from sgp.documents import content, layouts
from sgp.subdocuments import services
from sgp.vocab.models import Term
from tests.documents.conftest import entry_topics

pytestmark = [pytest.mark.django_db]


def chain(project, make_subdocument, approve_quick, until=None):
    for code in (
        "formulacao",
        "lote-piloto",
        "rapd",
        "analise-critica",
        "validacao",
        "verificacao-final",
    ):
        if code == until:
            break
        approve_quick(make_subdocument(project, code))


def build(sub):
    return content.build("subdocument", sub, layouts.layout_for("subdocument", sub.pk, sub.version))


@pytest.mark.req("006:FR-001")
@pytest.mark.req("006:FR-004")
def test_capa_da_entrada_com_os_dados_do_sistema(complete_entry):
    data = build(complete_entry)
    assert data["title"] == "Entrada de Projeto"
    assert data["product"] == complete_entry.project.product_name.upper()
    assert data["version"] == "01"
    assert data["form_footer"] == (
        "Formulário Versão: 05. Referência: PSG 20 - Pesquisa e Desenvolvimento de Produtos"
    )
    cover = data["cover"]
    assert cover["columns"] == 2 and len(cover["topics"]) == 13
    assert cover["topics"][0] == [1, "Amostras"] and cover["topics"][-1][0] == 13
    assert cover["approver_label"] == "Gestor de P&D:"
    assert data["signatures"] == [] and data["approved_on"] == ""


@pytest.mark.req("006:FR-006")
@pytest.mark.req("006:FR-007")
@pytest.mark.req("006:FR-009")
def test_corpo_com_topicos_e_tabelas_numerados(complete_entry, standard):
    data = build(complete_entry)
    sections = {section["label"]: section for section in data["sections"]}
    assert [s["number"] for s in data["sections"]] == list(range(1, 14))
    filters = next(s for s in data["sections"] if s["not_applicable"])
    assert filters["justification"] == "Método sem leitura óptica" and filters["blocks"] == []
    tables = [b for s in data["sections"] for b in s["blocks"] if b["kind"] == "table"]
    assert [t["number"] for t in tables] == [f"Tabela {n:02d}" for n in range(1, len(tables) + 1)]
    regulatory = next(s for s in data["sections"] if s["number"] == 11)
    assert any(
        standard.identifier in line for b in regulatory["blocks"] for line in b.get("lines", [])
    )
    assert sections  # rótulos resolvidos


@pytest.mark.req("006:FR-010")
def test_campo_obrigatorio_vazio_aparece_como_nao_preenchido(project, make_subdocument):
    draft = make_subdocument(project, "entrada")
    blocks = [b for s in build(draft)["sections"] for b in s["blocks"]]
    assert any(b["kind"] == "empty" and b["text"] == "(não preenchido)" for b in blocks)


@pytest.mark.req("006:FR-010")
def test_formulario_opcional_sai_sem_numero_com_caixas(complete_entry, analyst, standard):
    topics = entry_topics(standard.pk)
    topics["formulario_opcional"] = {
        "na": False,
        "justification": "",
        "values": {"analito": "Glicose", "classificacao_teste": "quantitativo"},
    }
    sub = services.save_subdocument(complete_entry, by=analyst, data={"topics": topics})
    form = build(sub)["optional_form"]
    assert form["title"] == "Formulário opcional de entrada"
    assert "Analito: Glicose" in form["lines"]
    options = form["groups"][0]["options"]
    assert [o["checked"] for o in options].count(True) == 1
    assert all(s["label"] != "Formulário opcional de entrada" for s in build(sub)["sections"])


@pytest.mark.req("006:FR-005")
def test_saida_lista_todos_os_setores_marcando_os_escolhidos(
    project, approved_entry, make_subdocument, approve_quick, analyst
):
    chain(project, make_subdocument, approve_quick)
    exit_doc = make_subdocument(project, "saida")
    exit_doc = services.save_subdocument(
        exit_doc,
        by=analyst,
        data={
            "topics": {
                "setores": {"na": False, "justification": "", "values": {"setores": ["sac"]}}
            }
        },
    )
    data = build(exit_doc)
    sectors = [item for column in data["cover"]["sectors"]["columns"] for item in column]
    total = Term.objects.of("setor-transferencia").filter(is_active=True).count()
    assert len(sectors) == total and [s["label"] for s in sectors if s["checked"]] == ["SAC"]
    assert len(data["cover"]["topics"]) == 10  # projeto ANVISA: itens só do MAPA não aparecem


@pytest.mark.req("006:FR-005")
def test_verificacao_final_leva_a_check_list_para_a_capa(
    project, approved_entry, make_subdocument, approve_quick
):
    chain(project, make_subdocument, approve_quick, until="verificacao-final")
    check = make_subdocument(project, "verificacao-final")
    data = build(check)
    checklist = data["cover"]["checklist"]
    assert checklist["title"] == "CHECK LIST"
    assert checklist["columns"] == [
        "REQUISITOS DE ENTRADA",
        "PREVISTO",
        "REALIZADO",
        "DISPOSIÇÃO (APROVADO, REPROVADO OU OUTROS)",
    ]
    assert checklist["rows"][0][0] == "1 - Amostras"
    assert data["cover"]["topics"] == [] and data["sections"] == []


@pytest.mark.req("006:FR-005")
def test_alteracao_e_validacao_com_as_particularidades_da_capa(
    project, approved_entry, make_subdocument, approve_quick
):
    change = make_subdocument(project, "alteracao")
    data = build(change)
    assert (data["changed_version"], data["new_version"]) == ("01", "02")
    chain(project, make_subdocument, approve_quick, until="validacao")
    validation = make_subdocument(project, "validacao")
    assert build(validation)["cover"]["approver_label"] == (
        "Gestor de P&D responsável pela Aprovação:"
    )
