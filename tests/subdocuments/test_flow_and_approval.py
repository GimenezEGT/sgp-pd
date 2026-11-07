"""Ordem do fluxo, autorização do gestor e aprovação provisória (FR-015, FR-016 da feature 004)."""

import time

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from sgp.accounts.profiles import Profile
from sgp.catalog.models import Material
from sgp.subdocuments import flow, services
from sgp.subdocuments.models import FlowAuthorizationUse, Subdocument
from sgp.vocab.models import get_term

pytestmark = [pytest.mark.django_db]


def term(code):
    return get_term("tipo-subdocumento", code)


@pytest.mark.req("004:FR-016")
def test_entrada_aprovada_e_exigida_sem_dispensa(project, make_subdocument, manager):
    make_subdocument(project, "entrada")
    with pytest.raises(ValidationError, match="Entrada de Projeto aprovada"):
        make_subdocument(project, "formulacao")
    with pytest.raises(ValidationError, match="não pode ser dispensada"):
        services.authorize_flow(project, term("formulacao"), by=manager, reason="Urgente")
    with pytest.raises(ValidationError, match="Entrada de Projeto aprovada"):
        make_subdocument(project, "alteracao")


@pytest.mark.req("004:FR-016")
def test_fora_da_ordem_pede_autorizacao_do_gestor(
    project, approved_entry, make_subdocument, manager, events
):
    make_subdocument(project, "formulacao")
    with pytest.raises(
        services.FlowAuthorizationRequired, match="Elaboração de Formulação aprovada"
    ):
        make_subdocument(project, "lote-piloto")
    with pytest.raises(ValidationError, match="motivo"):
        services.authorize_flow(project, term("lote-piloto"), by=manager, reason=" ")
    authorization = services.authorize_flow(
        project, term("lote-piloto"), by=manager, reason="Lote piloto em paralelo por prazo"
    )
    pilot = make_subdocument(project, "lote-piloto")
    assert FlowAuthorizationUse.objects.get(authorization=authorization).subdocument == pilot
    assert services._authorization(project, term("lote-piloto")) is None
    event = events("subdocuments.flow_authorized")[-1]
    assert event.reason == "Lote piloto em paralelo por prazo"
    assert event.new_value["falta"] == "Elaboração de Formulação aprovada"


@pytest.mark.req("004:FR-016")
def test_autorizacao_so_quando_falta_algo_e_so_pelo_gestor(
    project, approved_entry, make_subdocument, analyst
):
    with pytest.raises(ValidationError, match="Só o Gestor"):
        services.authorize_flow(project, term("lote-piloto"), by=analyst, reason="x")
    assert flow.requirement(project, "formulacao") is None


@pytest.mark.req("004:FR-015")
def test_aprovacao_provisoria(
    project, approved_entry, make_subdocument, analyst, manager, make_material, events
):
    formulation = make_subdocument(project, "formulacao")
    with pytest.raises(ValidationError) as missing:
        services.approve(formulation, by=manager)
    assert any("obrigatório" in message for message in missing.value.messages)
    material = make_material(analyst, code="MP-APR")
    services.save_subdocument(
        formulation,
        by=analyst,
        data={
            "topics": {
                "reagentes": {
                    "na": False,
                    "justification": "",
                    "values": {"reagentes": [{"numero": "R1", "nome": "Tampão", "composicao": ""}]},
                },
                "materias_primas": {
                    "na": False,
                    "justification": "",
                    "values": {
                        "itens": [
                            {"reagente": "R1", "insumo": {"id": material.pk, "code": "MP-APR"}}
                        ]
                    },
                },
                "modo_preparo": {
                    "na": False,
                    "justification": "",
                    "values": {"componentes": [], "passos": "Dissolver"},
                },
                "complementares": {"na": True, "justification": "Não há", "values": {"texto": ""}},
            }
        },
    )
    with pytest.raises(ValidationError, match="Só o Gestor"):
        services.approve(formulation, by=analyst)
    approved = services.approve(formulation, by=manager)
    assert approved.is_approved and approved.approved_by == manager
    assert Material.objects.get(pk=material.pk).is_locked
    assert events("subdocuments.approved")[-1].new_value["cadastros_bloqueados"] == 1
    with pytest.raises(ValidationError, match="aprovado e não pode ser editado"):
        services.save_subdocument(approved, by=analyst, data={"topics": {}})


@pytest.mark.req("004:FR-015")
def test_quem_criou_nao_aprova(project, approved_entry, make_subdocument, manager):
    own = make_subdocument(project, "formulacao", by=manager)
    with pytest.raises(ValidationError, match="Quem criou"):
        services.approve(own, by=manager)


@pytest.mark.req("004:FR-016")
def test_lista_do_projeto_mostra_ordem_e_autorizacao(client, project, approved_entry, manager):
    client.force_login(manager)
    page = client.get(reverse("subdocuments:project_list", args=[project.pk])).content.decode()
    assert "Falta: Elaboração de Formulação aprovada" in page
    assert "Autorizar fora da ordem" in page


@pytest.mark.req("004:SC-005")
def test_gravar_100_linhas_em_menos_de_2_segundos(
    project, approved_entry, make_subdocument, analyst
):
    formulation = make_subdocument(project, "formulacao")
    rows = [
        {
            "reagente": f"R{i}",
            "componente": f"Componente {i}",
            "peso_molecular": "58.44",
            "mg_l": "",
            "g_l": "",
            "mm": "",
            "insumo": None,
        }
        for i in range(100)
    ]
    start = time.monotonic()
    services.save_subdocument(
        formulation,
        by=analyst,
        data={
            "topics": {
                "modo_preparo": {
                    "na": False,
                    "justification": "",
                    "values": {"componentes": rows, "passos": "Preparo"},
                }
            }
        },
    )
    elapsed = time.monotonic() - start
    assert (
        len(
            Subdocument.objects.get(pk=formulation.pk).topic_data("modo_preparo")["values"][
                "componentes"
            ]
        )
        == 100
    )
    assert elapsed < 2, f"gravação levou {elapsed:.2f} s"


@pytest.mark.req("004:FR-015")
def test_aprovacao_pela_tela(client, project, approved_entry, make_user):
    other_manager = make_user(None, Profile.RD_MANAGER)
    client.force_login(other_manager)
    page = client.get(reverse("subdocuments:detail", args=[approved_entry.pk])).content.decode()
    assert "Aprovado" in page and "Aprovar</button>" not in page
