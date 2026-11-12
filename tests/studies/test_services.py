"""Estudo, critério, medidas, cálculo, não aplicável e permissões (FR-001 a FR-005, FR-008,
FR-013, FR-017, FR-018, SC-002, SC-004)."""

import time

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse

from sgp.accounts.profiles import Profile
from sgp.studies import services
from sgp.studies.models import Study
from tests.studies.conftest import rows

pytestmark = [pytest.mark.django_db]


@pytest.mark.req("007:FR-001")
@pytest.mark.req("007:FR-002")
def test_tipo_controlado_versao_e_vinculo(make_study, rapd, study_type, project, analyst):
    study = make_study("repetibilidade", subdocument=rapd, topic_key="testes_preliminares")
    assert study.version == 1 and study.subdocument == rapd and study.results["global"]
    from sgp.vocab.models import get_term

    with pytest.raises(ValidationError, match="lista controlada"):
        services.create_study(
            project, by=analyst, data={"study_type": get_term("tipo-amostra", "soro"), "title": "x"}
        )
    with pytest.raises(ValidationError, match="tópico"):
        make_study("repetibilidade", subdocument=rapd, topic_key="inexistente")


@pytest.mark.req("007:FR-003")
def test_criterio_congelado_depois_da_primeira_medida(make_study, analyst):
    study = make_study()
    study = services.set_criteria(
        study, by=analyst, criteria=[{"metrica": "cv", "comparacao": "lt", "limite": "15"}]
    )
    assert study.criteria == [{"metrica": "cv", "comparacao": "lt", "limite": "15"}]
    with pytest.raises(ValidationError, match="métrica"):
        services.set_criteria(
            study, by=analyst, criteria=[{"metrica": "r2", "comparacao": "lt", "limite": "1"}]
        )
    study = services.save_rows(study, by=analyst, raw_rows=rows([2, 4, 4, 4, 5, 5, 7, 9]))
    with pytest.raises(ValidationError, match="não muda depois"):
        services.set_criteria(
            study, by=analyst, criteria=[{"metrica": "cv", "comparacao": "lt", "limite": "50"}]
        )
    assert study.results["criterios"][0]["atendido"] is False


@pytest.mark.req("007:FR-005")
@pytest.mark.req("007:FR-008")
def test_medidas_com_cadastros_e_resultados_recalculados(
    make_study, analyst, make_lot, project, events
):
    lot = make_lot(project, analyst, code="L-EST-1")
    study = make_study("entre-lotes")
    study = services.save_rows(
        study,
        by=analyst,
        raw_rows=[{"lote": "L-EST-1", "y": "10,0"}, {"lote": "L-EST-1", "y": "12,0"}],
    )
    assert study.rows[0]["lote"] == {"id": lot.pk, "codigo": "L-EST-1"}
    assert services.summary(study)["media"] == "11.00"
    with pytest.raises(ValidationError) as error:
        services.save_rows(
            study, by=analyst, raw_rows=[{"lote": "NAO-EXISTE", "y": "1"}, {"y": "x"}]
        )
    assert any("Linha 1" in m and "não existe" in m for m in error.value.messages)
    assert any("Linha 2" in m for m in error.value.messages)
    assert events("studies.updated")[-1].new_value["linhas"] == 2
    assert "media" not in [
        f.name for f in Study._meta.get_fields()
    ]  # nenhum campo de valor calculado


@pytest.mark.req("007:FR-013")
@pytest.mark.req("007:SC-002")
def test_nao_aplicavel_exige_justificativa_e_exclui_medidas(make_study, analyst):
    study = make_study("efeito-prozona")
    with pytest.raises(ValidationError, match="justificativa"):
        services.mark_not_applicable(study, by=analyst, justification=" ")
    study = services.mark_not_applicable(study, by=analyst, justification="Método não imunológico")
    assert study.not_applicable and study.results == {}
    with pytest.raises(ValidationError, match="não aplicável"):
        services.save_rows(study, by=analyst, raw_rows=[{"grupo": "A", "obtido": "pos"}])
    other = services.save_rows(make_study("repetibilidade"), by=analyst, raw_rows=rows([1, 2]))
    with pytest.raises(ValidationError, match="resultados lançados"):
        services.mark_not_applicable(other, by=analyst, justification="x")


@pytest.mark.req("007:FR-017")
def test_so_editores_do_projeto_alteram_e_acesso_negado_registrado(
    make_study, make_user, client, events, project
):
    study = make_study()
    outsider = make_user(None, Profile.ANALYST)
    with pytest.raises(PermissionDenied):
        services.save_rows(study, by=outsider, raw_rows=rows([1]))
    client.force_login(outsider)
    assert client.get(reverse("studies:detail", args=[study.pk])).status_code == 403
    assert client.get(reverse("studies:project_list", args=[project.pk])).status_code == 403
    assert len(events("auth.permission_denied")) == 2


@pytest.mark.req("007:FR-018")
@pytest.mark.req("007:FR-002")
def test_telas_de_criacao_criterio_e_medidas(client, analyst, project, study_type):
    client.force_login(analyst)
    response = client.post(
        reverse("studies:project_list", args=[project.pk]),
        {
            "study_type": study_type("repetibilidade").pk,
            "title": "Repetibilidade do controle",
            "link": "",
            "rounding": "half_even",
            "ci_method": "clopper_pearson",
            "cutoff": "",
            "cutoff_direction": "ge",
        },
    )
    study = Study.objects.get(title="Repetibilidade do controle")
    assert response.status_code == 302
    url = reverse("studies:edit", args=[study.pk])
    client.post(
        url,
        {
            "acao": "criterios",
            "c__0__metrica": "cv",
            "c__0__comparacao": "lt",
            "c__0__limite": "15",
        },
    )
    data = {"acao": "linhas", "row_version": Study.objects.get(pk=study.pk).row_version}
    for index, value in enumerate((2, 4, 4, 4, 5, 5, 7, 9)):
        data[f"r__{index}__y"] = str(value)
    client.post(url, data)
    page = client.get(reverse("studies:detail", args=[study.pk])).content.decode()
    assert "42,76" in page and "não atendido" in page and "2,14" in page


@pytest.mark.req("007:SC-004")
def test_500_medidas_em_menos_de_2_segundos(make_study, analyst):
    study = make_study("reprodutibilidade")
    raw = [{"dia": str(1 + i % 5), "y": f"{100 + (i % 17)},5"} for i in range(500)]
    start = time.perf_counter()
    study = services.save_rows(study, by=analyst, raw_rows=raw)
    assert time.perf_counter() - start < 2
    assert len(study.rows) == 500


@pytest.mark.req("007:FR-004")
@pytest.mark.req("007:FR-011")
def test_regra_de_arredondamento_e_metodo_do_ic_registrados_no_estudo(make_study, analyst):
    default = make_study("repetibilidade")
    assert (default.rounding, default.places, default.fine_places, default.ci_method) == (
        "half_even",
        2,
        4,
        "clopper_pearson",
    )
    study = make_study("sensibilidade-especificidade", rounding="half_up", ci_method="wilson")
    raw = [{"esperado": "pos", "obtido": "pos"}] * 45 + [{"esperado": "pos", "obtido": "neg"}] * 5
    study = services.save_rows(study, by=analyst, raw_rows=raw)
    sens = next(i for i in study.results["global"] if i["metrica"] == "sensibilidade")
    assert sens["regra"] == "meio para cima, 2 casas" and sens["ic"] == ["78.64", "95.65"]
