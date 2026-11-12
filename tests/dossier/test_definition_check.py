"""Definição declarativa e checagem item a item (FR-001 a FR-003, FR-009)."""

import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from sgp.dossier import check, definition, services

ROMANS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]


@pytest.mark.req("011:FR-002")
def test_definicao_padrao_tem_a_estrutura_i_a_xii():
    parsed = definition.parse(definition.default_yaml())
    assert [item["numero"] for item in parsed["itens"]] == ROMANS
    keys = [item["key"] for item, _ in definition.leaves(parsed["itens"])]
    assert "I.A.1" in keys and "VI.D" in keys and "XII" in keys and len(keys) == len(set(keys))


@pytest.mark.req("011:FR-002")
@pytest.mark.parametrize(
    "text,message",
    [
        ("itens: [{numero: I, titulo: X}]", "ao menos uma fonte"),
        ("itens: [{numero: I, titulo: X, fontes: [{tipo: inventado}]}]", "tipo válido"),
        (
            "itens: [{numero: I, titulo: X, classes: [V], fora_da_classe: y, fontes: [{tipo: normas}]}]",
            "classes válidas",
        ),
        (
            "itens: [{numero: I, titulo: X, classes: [II], fontes: [{tipo: normas}]}]",
            "fora_da_classe",
        ),
        (
            "itens: [{numero: I, titulo: X, fontes: [{tipo: normas}]}, {numero: I, titulo: Y, fontes: [{tipo: normas}]}]",
            "repetido",
        ),
        (
            "itens: [{numero: I, titulo: X, fontes: [{tipo: subdocumento}]}]",
            "subdocumento e tópico",
        ),
        ("itens: [", "YAML inválido"),
    ],
)
def test_definicao_invalida_e_recusada(text, message):
    with pytest.raises(ValidationError, match=message):
        definition.parse(text)


@pytest.mark.req("011:FR-002")
def test_so_a_qualidade_publica_nova_definicao(quality, member, events):
    record = services.publish_definition(by=quality, text=definition.default_yaml(), note="Revisão")
    assert record.version == 2 and services.current_definition() == record
    with pytest.raises(PermissionDenied):
        services.publish_definition(by=member, text=definition.default_yaml())
    assert len(events("dossier.definition_published")) == 1


@pytest.mark.req("011:FR-001")
@pytest.mark.req("011:FR-003")
def test_checagem_por_classe_com_origem_e_situacao(
    signed_project, approved_entry_with_class, quality, minimal_definition, approved_text
):
    approved_entry_with_class("II")
    result = services.checklist(signed_project)
    items = {item["key"]: item for item in result["items"]}
    assert result["risk_class"] == "II"
    assert items["I.A"]["status"] == "complete" and "Entrada de Projeto" in items["I.A"]["origin"]
    assert (
        items["II"]["status"] == "complete"
        and items["II"]["annexes"][0].original_name == "matriz-risco.pdf"
    )
    assert items["III"]["status"] == "complete"
    assert items["IV"]["status"] == "na" and "classes III e IV" in items["IV"]["justification"]
    assert items["I.B"]["status"] == "missing" and "Complemento" in items["I.B"]["origin"]
    assert items["V"]["status"] == "missing"
    approved_text()
    assert {i["key"]: i["status"] for i in services.checklist(signed_project)["items"]}[
        "V"
    ] == "complete"


@pytest.mark.req("011:FR-003")
def test_nao_aplicavel_exige_justificativa(
    signed_project, approved_entry_with_class, quality, minimal_definition
):
    approved_entry_with_class("II")
    with pytest.raises(ValidationError, match="justificativa"):
        services.save_supplement(
            signed_project,
            by=quality,
            item_key="I.B",
            text="",
            not_applicable=True,
            justification="",
        )
    services.save_supplement(
        signed_project,
        by=quality,
        item_key="I.B",
        text="",
        not_applicable=True,
        justification="Kit sem analito único",
    )
    items = {i["key"]: i for i in services.checklist(signed_project)["items"]}
    assert (
        items["I.B"]["status"] == "na" and items["I.B"]["justification"] == "Kit sem analito único"
    )
    services.publish_definition(
        by=quality,
        text="itens: [{numero: I, titulo: Filtros, fontes: [{tipo: subdocumento, subdocumento: entrada, topico: filtros}]}]",
    )
    only = services.checklist(signed_project)["items"][0]
    assert only["status"] == "na" and only["justification"] == "Método sem leitura óptica"


@pytest.mark.req("011:FR-001")
def test_classe_i_e_classe_ausente(signed_project, approved_entry_with_class, quality):
    result = services.checklist(signed_project)
    assert result["risk_class"] is None
    assert all(item["status"] == "missing" for item in result["items"])
    approved_entry_with_class("I")
    items = {i["key"]: i for i in services.checklist(signed_project)["items"]}
    assert items["VI.C"]["status"] == "na" and "classes II a IV" in items["VI.C"]["justification"]
    assert items["VIII.A"]["status"] == "na"


@pytest.mark.req("011:FR-009")
def test_familia_com_dois_kits(
    signed_project,
    approved_entry_with_class,
    make_project,
    fill_project,
    manager,
    signing,
    member,
    quality,
    minimal_definition,
):
    from sgp.projects import services as project_services
    from sgp.projects.models import Project
    from sgp.signatures import services as signatures

    Project.objects.filter(pk=signed_project.pk).update(product_family="Linha Fictícia")
    signed_project.refresh_from_db()
    other = fill_project(
        make_project(
            title="Segundo kit", product_name="KIT DOIS", product_family="Linha Fictícia"
        )
    )
    signing.enable(other.leader, manager)
    signatures.submit_project(other, by=other.leader, password=signing.password)
    signatures.approve_project(other, by=manager, password=signing.password)
    other.refresh_from_db()
    project_services.add_member(other, by=other.leader, user=member, role="Analista")
    approved_entry_with_class("II")
    approved_entry_with_class("II", project=other)
    assert [kit.pk for kit in check.family(signed_project)] == sorted(
        [signed_project.pk, other.pk], key=lambda pk: Project.objects.get(pk=pk).code
    )
    assert check.subject(signed_project) == "Família Linha Fictícia"
    items = {i["key"]: i for i in services.checklist(signed_project)["items"]}
    kits = [b["lines"][0] for b in items["I.A"]["blocks"] if b.get("label") == "Kit"]
    assert sorted(kits) == ["KIT DE TESTE", "KIT DOIS"]
