"""Criação e preenchimento de subdocumentos (US3: FR-008 a FR-014, SC-004 da feature 004)."""

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from sgp.accounts.profiles import Profile
from sgp.files import storage
from sgp.formtemplates.services import current_template
from sgp.subdocuments import permissions, services
from sgp.subdocuments.models import Subdocument
from sgp.vocab.models import get_term

pytestmark = [pytest.mark.django_db]

PDF = b"%PDF-1.4\nanexo de teste\n%%EOF\n"


@pytest.fixture
def formulation(project, approved_entry, make_subdocument):
    return make_subdocument(project, "formulacao")


def save(subdocument, by, topics, **kwargs):
    return services.save_subdocument(subdocument, by=by, data={"topics": topics}, **kwargs)


@pytest.mark.req("004:FR-008")
def test_cria_em_rascunho_na_versao_01_com_o_modelo_vigente(formulation, events):
    assert formulation.is_draft and formulation.version_display == "01"
    assert formulation.template == current_template(formulation.subdocument_type)
    assert (
        formulation.topic_data("nome_produto")["values"]["produto"]
        == formulation.project.product_name
    )
    event = events("subdocuments.created")[-1]
    assert event.project_id == formulation.project_id
    assert event.new_value["modelo"] == "05"


@pytest.mark.req("004:FR-008")
def test_um_por_tipo_e_alteracoes_numeradas(project, formulation, make_subdocument):
    with pytest.raises(ValidationError, match="já tem"):
        make_subdocument(project, "formulacao")
    first, second = make_subdocument(project, "alteracao"), make_subdocument(project, "alteracao")
    assert (first.sequence, second.sequence) == (1, 2)


@pytest.mark.req("004:FR-009")
@pytest.mark.req("004:FR-012")
def test_rascunho_incompleto_e_gravado_com_trilha(formulation, analyst, events):
    saved = save(
        formulation,
        analyst,
        {
            "reagentes": {
                "na": False,
                "justification": "",
                "values": {"reagentes": [{"numero": "R1", "nome": "Tampão", "composicao": ""}]},
            }
        },
        row_version=1,
    )
    assert saved.row_version == 2
    event = events("subdocuments.updated")[-1]
    assert event.new_value["reagentes"]["values"]["reagentes"][0]["nome"] == "Tampão"
    assert services.completeness(saved)


@pytest.mark.req("004:FR-010")
@pytest.mark.req("004:SC-004")
def test_nao_aplicavel_exige_justificativa_e_campos_vazios(formulation, analyst):
    with pytest.raises(ValidationError, match="exige justificativa"):
        save(
            formulation,
            analyst,
            {"complementares": {"na": True, "justification": "", "values": {"texto": ""}}},
        )
    with pytest.raises(ValidationError, match="campos preenchidos"):
        save(
            formulation,
            analyst,
            {
                "complementares": {
                    "na": True,
                    "justification": "Sem dados",
                    "values": {"texto": "Algo escrito"},
                }
            },
        )
    saved = save(
        formulation,
        analyst,
        {"complementares": {"na": True, "justification": "Sem dados", "values": {"texto": ""}}},
    )
    assert saved.topic_data("complementares")["na"] is True


@pytest.mark.req("004:FR-010")
def test_topico_que_nao_aceita_nao_aplicavel(formulation, analyst):
    with pytest.raises(ValidationError, match="não aceita 'não aplicável'"):
        save(formulation, analyst, {"reagentes": {"na": True, "justification": "x", "values": {}}})


@pytest.mark.req("004:FR-012")
def test_edicao_simultanea_e_recusada(formulation, analyst):
    save(formulation, analyst, {}, row_version=1)
    with pytest.raises(ValidationError, match="Outra pessoa gravou"):
        save(formulation, analyst, {}, row_version=1)


@pytest.mark.req("004:FR-013")
def test_lote_de_outro_projeto_e_recusado(
    project,
    approved_entry,
    make_subdocument,
    analyst,
    open_project,
    make_lot,
    make_user,
    approve_quick,
):
    quality = make_user(None, Profile.QUALITY)
    foreign = make_lot(open_project(), quality, code="LP-OUT")
    own = make_lot(project, quality, code="LP-IN")
    approve_quick(make_subdocument(project, "formulacao"))
    pilot = make_subdocument(project, "lote-piloto")
    with pytest.raises(ValidationError, match="não pode ser escolhido"):
        save(
            pilot,
            analyst,
            {
                "lote": {
                    "na": False,
                    "justification": "",
                    "values": {"produto": "KIT", "lotes": [foreign.pk]},
                }
            },
        )
    saved = save(
        pilot,
        analyst,
        {
            "lote": {
                "na": False,
                "justification": "",
                "values": {"produto": "KIT", "lotes": [own.pk]},
            }
        },
    )
    assert saved.topic_data("lote")["values"]["lotes"] == [own.pk]


@pytest.mark.req("004:FR-014")
def test_anexo_com_politica_do_projeto(project, approved_entry, analyst, make_user):
    entry = approved_entry
    assert entry.is_approved
    from sgp.subdocuments.models import Subdocument as Model

    draft_entry = Model.objects.get(pk=entry.pk)
    stored = storage.store_upload(SimpleUploadedFile("matriz.pdf", PDF), by=analyst)
    data = dict(draft_entry.data)
    data["files"] = [stored.pk]
    Model.objects.filter(pk=entry.pk).update(data=data)
    assert permissions.subdocument_file_policy(analyst, stored)
    assert not permissions.subdocument_file_policy(make_user(None, Profile.ANALYST), stored)


@pytest.mark.req("004:FR-014")
def test_anexo_pela_tela_e_download_pela_politica_do_projeto(
    client, project, analyst, make_subdocument, login_as, events
):
    entry = make_subdocument(project, "entrada")
    client.force_login(analyst)
    response = client.post(
        reverse("subdocuments:edit", args=[entry.pk]),
        {
            "row_version": entry.row_version,
            "t__gerenciamento_risco__descricao": "Matriz anexa",
            "t__gerenciamento_risco__matriz__novo": SimpleUploadedFile("matriz.pdf", PDF),
        },
    )
    assert response.status_code == 302
    entry.refresh_from_db()
    file_id = entry.topic_data("gerenciamento_risco")["values"]["matriz"][0]
    assert entry.data["files"] == [file_id]
    assert events("files.uploaded")[-1].new_value["nome"] == "matriz.pdf"
    assert client.get(reverse("files:download", args=[file_id])).content == PDF
    client.logout()
    login_as(Profile.ANALYST)
    assert client.get(reverse("files:download", args=[file_id])).status_code == 403
    client.logout()
    client.force_login(analyst)
    client.post(
        reverse("subdocuments:edit", args=[entry.pk]),
        {"row_version": entry.row_version, "t__gerenciamento_risco__descricao": "Sem matriz"},
    )
    entry.refresh_from_db()
    assert entry.topic_data("gerenciamento_risco")["values"]["matriz"] == []


@pytest.mark.req("004:FR-008")
def test_sem_acesso_ao_projeto_e_negado_e_registrado(client, formulation, login_as, events):
    login_as(Profile.ANALYST)
    response = client.get(reverse("subdocuments:detail", args=[formulation.pk]))
    assert response.status_code == 403
    assert events("auth.permission_denied")


@pytest.mark.req("004:FR-008")
@pytest.mark.parametrize("profile", [Profile.QUALITY, Profile.READER])
def test_quem_nao_edita(project, make_user, profile):
    from sgp.projects import services as project_services

    user = make_user(None, profile)
    project_services.add_member(project, by=project.leader, user=user, role="Consulta")
    assert permissions.can_view(user, project)
    assert not permissions.can_edit(user, project)


@pytest.mark.req("004:FR-009")
def test_edicao_pela_tela_com_tabela_e_lista(client, formulation, analyst, events):
    client.force_login(analyst)
    url = reverse("subdocuments:edit", args=[formulation.pk])
    response = client.post(
        url,
        {
            "row_version": formulation.row_version,
            "t__nome_produto__produto": "KIT DE TESTE",
            "t__reagentes__reagentes__0__numero": "R1",
            "t__reagentes__reagentes__0__nome": "Tampão",
            "t__reagentes__reagentes__0__composicao": "Tris",
            "t__modo_preparo__passos": "Dissolver.\n\n- passo 1\n- passo 2",
            "t__complementares__na": "1",
            "t__complementares__justificativa": "Sem informações complementares",
        },
    )
    assert response.status_code == 302
    formulation.refresh_from_db()
    assert formulation.topic_data("reagentes")["values"]["reagentes"][0]["nome"] == "Tampão"
    detail = client.get(reverse("subdocuments:detail", args=[formulation.pk])).content.decode()
    assert "Tabela 01" in detail and "<li>passo 1</li>" in detail
    row = client.get(
        reverse("subdocuments:row", args=[formulation.pk]),
        {"topico": "reagentes", "campo": "reagentes"},
    )
    assert row.status_code == 200 and "t__reagentes__reagentes__" in row.content.decode()


@pytest.mark.req("004:FR-013")
def test_referencia_aponta_para_a_versao(
    project, approved_entry, analyst, manager, make_subdocument, make_material, approve_quick
):
    from sgp.catalog import versioning

    material = make_material(analyst, code="MP-REF")
    formulation = make_subdocument(project, "formulacao")
    save(
        formulation,
        analyst,
        {
            "materias_primas": {
                "na": False,
                "justification": "",
                "values": {
                    "itens": [{"reagente": "R1", "insumo": {"id": material.pk, "code": "MP-REF"}}]
                },
            }
        },
    )
    versioning.lock_version(material, by=manager, reason="Outro documento assinado")
    versioning.update_record(
        material, by=manager, data={"description": "Nova descrição"}, reason="Correção"
    )
    formulation.refresh_from_db()
    cell = formulation.topic_data("materias_primas")["values"]["itens"][0]["insumo"]
    assert cell["id"] == material.pk
    assert Subdocument.objects.filter(pk=formulation.pk).exists()
    assert get_term("tipo-subdocumento", "formulacao") == formulation.subdocument_type
