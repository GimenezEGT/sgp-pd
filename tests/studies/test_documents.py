"""Estudos nos documentos, assinatura, bloqueio e versões (FR-014 a FR-016, SC-003)."""

import pytest
from django.core.exceptions import ValidationError

from sgp.documents import content, layouts
from sgp.signatures.documents import get_adapter
from sgp.studies import services
from sgp.studies.models import Study
from tests.studies.conftest import rows

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def linked(rapd, make_study, analyst):
    study = make_study("repetibilidade", subdocument=rapd, topic_key="testes_preliminares")
    study = services.set_criteria(
        study, by=analyst, criteria=[{"metrica": "cv", "comparacao": "lt", "limite": "15"}]
    )
    study = services.save_rows(study, by=analyst, raw_rows=rows([2, 4, 4, 4, 5, 5, 7, 9]))
    na = make_study("efeito-prozona", subdocument=rapd, topic_key="testes_preliminares")
    na = services.mark_not_applicable(na, by=analyst, justification="Método não imunológico")
    return study, na


@pytest.mark.req("007:FR-014")
@pytest.mark.req("007:SC-002")
def test_tabelas_numeradas_e_conclusao_no_documento(rapd, linked):
    data = content.build("subdocument", rapd, layouts.layout_for("subdocument", rapd.pk, 1))
    section = next(s for s in data["sections"] if s["label"] == "Testes e avaliações preliminares")
    tables = [b for b in section["blocks"] if b["kind"] == "table"]
    assert [t["label"] for t in tables] == [
        "Medidas – Estudo de repetibilidade",
        "Resultados – Estudo de repetibilidade",
    ]
    assert all(t["number"].startswith("Tabela ") for t in tables)
    values = [line for b in section["blocks"] if b["kind"] == "values" for line in b["lines"]]
    assert any("CV% < 15: não atendido (42,76)" in line for line in values)
    assert "Método não imunológico" in values


@pytest.mark.req("007:FR-015")
def test_resumo_assinado_cobre_os_estudos(rapd, linked, analyst):
    snapshot = get_adapter("subdocument").snapshot(rapd)
    assert [s["tipo"] for s in snapshot["estudos"]] == ["efeito-prozona", "repetibilidade"] or [
        s["tipo"] for s in snapshot["estudos"]
    ] == ["repetibilidade", "efeito-prozona"]
    study = linked[0]
    services.save_rows(study, by=analyst, raw_rows=rows([1, 2, 3]))
    changed = get_adapter("subdocument").snapshot(rapd)
    assert changed != snapshot


@pytest.mark.req("007:FR-015")
@pytest.mark.req("007:FR-016")
@pytest.mark.req("007:SC-003")
def test_aprovacao_bloqueia_e_nova_versao_preserva_a_anterior(
    rapd, linked, analyst, manager, signing, events
):
    from sgp.signatures.models import ApprovedVersion
    from sgp.subdocuments import services as subdocuments

    def topic(values, na=False, justification=""):
        return {"na": na, "justification": justification, "values": values}

    subdocuments.save_subdocument(
        rapd,
        by=analyst,
        data={
            "topics": {
                "formulacoes": topic({"texto": "Formulação F1"}),
                "testes_preliminares": topic({"texto": "Ver estudos vinculados."}),
                "referencias": topic({}, na=True, justification="Sem referências"),
                "exatidao": topic({"texto": "Comparação com o kit de referência."}),
            }
        },
    )
    rapd.refresh_from_db()
    assert subdocuments.completeness(rapd) == []
    signing.submit_and_approve("subdocument", rapd, analyst, manager)
    study = Study.objects.get(pk=linked[0].pk)
    assert study.is_locked and events("studies.locked")
    with pytest.raises(ValidationError, match="bloqueado"):
        services.save_rows(study, by=analyst, raw_rows=rows([1, 2]))
    with pytest.raises(ValidationError, match="motivo"):
        services.new_version(study, by=analyst, reason="")
    new = services.new_version(study, by=analyst, reason="Recalcular com nova replicata")
    assert new.version == 2 and new.rows == study.rows and not new.is_locked
    approved = ApprovedVersion.objects.get(kind="subdocument", object_id=rapd.pk, version=1)
    assert (
        approved.content["estudos"][0]["versao"] == 1
        or approved.content["estudos"][1]["versao"] == 1
    )
