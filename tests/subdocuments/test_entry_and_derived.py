"""Entrada, Validação e Verificação Final (US4, US5: FR-017 a FR-019, SC-003 da feature 004)."""

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from sgp.subdocuments import derived, services
from tests.subdocuments.conftest import entry_topics

pytestmark = [pytest.mark.django_db]


@pytest.mark.req("004:FR-017")
def test_entrada_mostra_13_topicos_e_o_formulario_opcional(
    client, project, analyst, make_subdocument
):
    entry = make_subdocument(project, "entrada")
    client.force_login(analyst)
    page = client.get(reverse("subdocuments:edit", args=[entry.pk])).content.decode()
    assert "13. Outros dados pertinentes" in page
    assert "9. Classificação de Risco (RDC 830/2023)" in page
    assert "Formulário opcional de entrada" in page and "ISO 13485/2016" in page
    assert "Efeito prozona" in page and "Soro" in page


@pytest.mark.req("004:FR-017")
def test_classe_de_risco_vem_do_projeto(project, make_subdocument):
    entry = make_subdocument(project, "entrada")
    values = entry.topic_data("classificacao_risco")["values"]
    assert values == {"classe": project.risk_class, "regra": project.classification_rule}


@pytest.mark.req("004:FR-017")
def test_nao_se_aplica_sem_justificativa_e_recusado(project, analyst, standard, make_subdocument):
    entry = make_subdocument(project, "entrada")
    topics = entry_topics(standard.pk)
    topics["requisitos_desempenho"]["values"]["requisitos"][2]["justificativa"] = ""
    with pytest.raises(ValidationError, match="'não se aplica' exige justificativa"):
        services.save_subdocument(entry, by=analyst, data={"topics": topics})


@pytest.mark.req("004:FR-017")
def test_entrada_pela_tela_com_aplica(client, project, analyst, make_subdocument):
    entry = make_subdocument(project, "entrada")
    client.force_login(analyst)
    response = client.post(
        reverse("subdocuments:edit", args=[entry.pk]),
        {
            "row_version": entry.row_version,
            "t__amostras__tipos": ["soro", "plasma"],
            "t__requisitos_desempenho__requisitos__exatidao__aplica": "sim",
            "t__requisitos_desempenho__requisitos__exatidao__criterio": "Bias < 5%",
            "t__requisitos_desempenho__requisitos__precisao__aplica": "nao",
            "t__requisitos_desempenho__requisitos__precisao__justificativa": "",
        },
    )
    assert "marcado &#x27;não se aplica&#x27; exige justificativa" in response.content.decode()


@pytest.mark.req("004:FR-018")
def test_validacao_traz_pendencias_dos_requisitos(
    project, approved_entry, make_subdocument, approve_quick
):
    for code in ("formulacao", "lote-piloto", "rapd", "analise-critica"):
        approve_quick(make_subdocument(project, code))
    validation = make_subdocument(project, "validacao")
    rows = validation.topic_data("dados_desenvolvimento")["values"]["pendencias"]["rows"]
    applies = [row for row in rows if row["editable"]]
    assert [row["ref"] for row in applies] == ["exatidao", "precisao"]
    assert applies[0]["fixed"]["criterio"] == "Critério exatidao"
    not_applies = [row for row in rows if not row["editable"]]
    assert len(not_applies) == 14
    assert not_applies[0]["fixed"]["situacao"] == "Não se aplica: Não se aplica ao método"
    missing = services.completeness(validation)
    assert any("Evidência (estudo ou documento) obrigatório" in item for item in missing)


@pytest.mark.req("004:FR-019")
@pytest.mark.req("004:SC-003")
def test_verificacao_final_nasce_da_entrada_aprovada(
    project, approved_entry, make_subdocument, approve_quick
):
    for code in ("formulacao", "lote-piloto", "rapd", "analise-critica", "validacao"):
        approve_quick(make_subdocument(project, code))
    final = make_subdocument(project, "verificacao-final")
    rows = final.topic_data("checklist")["values"]["requisitos"]["rows"]
    assert len(rows) == 11
    assert rows[0]["label"] == "Amostras"
    assert rows[0]["fixed"]["previsto"] == derived.topic_summary(
        approved_entry.template.topic("amostras"), approved_entry.topic_data("amostras")
    )
    assert rows[0]["fixed"]["previsto"].startswith("Tipos de amostra: Soro")
    assert rows[7]["fixed"]["previsto"] == "Não aplicável: Método sem leitura óptica"
    assert rows[8]["label"] == "Classificação de Risco (RDC 830/2023)"


@pytest.mark.req("004:FR-019")
def test_verificacao_final_exige_entrada_aprovada(project, make_subdocument, manager):
    make_subdocument(project, "entrada")
    with pytest.raises(ValidationError, match="Entrada de Projeto aprovada"):
        make_subdocument(project, "verificacao-final")


@pytest.mark.req("004:FR-019")
def test_disposicao_sem_justificativa_e_atualizacao(
    project, approved_entry, make_subdocument, approve_quick, analyst
):
    for code in ("formulacao", "lote-piloto", "rapd", "analise-critica", "validacao"):
        approve_quick(make_subdocument(project, code))
    final = make_subdocument(project, "verificacao-final")
    value = final.topic_data("checklist")["values"]["requisitos"]
    value["rows"][0]["values"] = {
        "realizado": "Soro testado",
        "disposicao": "reprovado",
        "justificativa": "",
    }
    topics = {"checklist": {"na": False, "justification": "", "values": {"requisitos": value}}}
    with pytest.raises(ValidationError, match="exige justificativa"):
        services.save_subdocument(final, by=analyst, data={"topics": topics})
    value["rows"][0]["values"]["justificativa"] = "Plasma não testado"
    services.save_subdocument(final, by=analyst, data={"topics": topics})
    refreshed = services.refresh_derived(final, by=analyst)
    rows = refreshed.topic_data("checklist")["values"]["requisitos"]["rows"]
    assert rows[0]["values"]["justificativa"] == "Plasma não testado"


@pytest.mark.req("004:FR-018")
def test_analise_critica_traz_marcos(project, approved_entry, make_subdocument, approve_quick):
    for code in ("formulacao", "lote-piloto", "rapd"):
        approve_quick(make_subdocument(project, code))
    critical = make_subdocument(project, "analise-critica")
    milestones = critical.topic_data("evolucao")["values"]["marcos"]["rows"]
    assert milestones and milestones[0]["label"].startswith("Entrada de Projeto")
    assert milestones[0]["fixed"]["planejado"] == "15/12/2026"
