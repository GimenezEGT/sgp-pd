"""Fluxos dos subdocumentos pelas telas (FR-007, FR-015, FR-016, FR-019 da feature 004)."""

import pytest
from django.urls import reverse

from sgp.accounts.profiles import Profile
from sgp.subdocuments.models import FlowAuthorization, Subdocument

pytestmark = [pytest.mark.django_db]


@pytest.mark.req("004:FR-016")
def test_criar_autorizar_e_criar_fora_da_ordem(client, project, approved_entry, analyst, manager):
    client.force_login(analyst)
    new_url = reverse("subdocuments:new", args=[project.pk])
    response = client.post(new_url, {"tipo": "formulacao"})
    formulation = Subdocument.objects.get(project=project, subdocument_type__code="formulacao")
    assert response["Location"] == reverse("subdocuments:edit", args=[formulation.pk])
    response = client.post(new_url, {"tipo": "lote-piloto"}, follow=True)
    assert "A criação só segue com autorização" in response.content.decode()
    client.force_login(manager)
    client.post(
        reverse("subdocuments:authorize", args=[project.pk]),
        {"tipo": "lote-piloto", "motivo": "Paralelizar por prazo"},
    )
    assert FlowAuthorization.objects.filter(project=project).count() == 1
    client.force_login(analyst)
    client.post(new_url, {"tipo": "lote-piloto"})
    assert Subdocument.objects.filter(
        project=project, subdocument_type__code="lote-piloto"
    ).exists()


@pytest.mark.req("004:FR-008")
def test_quem_nao_edita_nao_cria_pela_tela(client, project, approved_entry, make_user):
    from sgp.projects import services as project_services

    quality = make_user(None, Profile.QUALITY)
    project_services.add_member(project, by=project.leader, user=quality, role="Qualidade")
    client.force_login(quality)
    assert client.get(reverse("subdocuments:project_list", args=[project.pk])).status_code == 200
    assert (
        client.post(
            reverse("subdocuments:new", args=[project.pk]), {"tipo": "formulacao"}
        ).status_code
        == 403
    )


@pytest.mark.req("004:FR-015")
def test_aprovar_e_migrar_pela_tela(
    client, project, approved_entry, analyst, manager, make_subdocument, make_user, publish_revision
):
    from sgp.formtemplates import services as template_services
    from sgp.vocab.models import get_term

    formulation = make_subdocument(project, "formulacao")
    client.force_login(manager)
    detail_url = reverse("subdocuments:detail", args=[formulation.pk])
    page = client.post(
        reverse("signatures:submit", args=["subdocument", formulation.pk]),
        {"senha": "qualquer"},
        follow=True,
    ).content.decode()
    assert "obrigatório" in page
    quality = make_user(None, Profile.QUALITY)
    draft = template_services.create_draft(get_term("tipo-subdocumento", "formulacao"), by=quality)
    template_services.update_draft(
        draft,
        by=quality,
        data={"reference": draft.reference + " (revisada)"},
        definition=draft.definition,
    )
    publish_revision("form", draft, quality)
    page = client.get(detail_url).content.decode()
    assert "Há versão mais nova do modelo (06)" in page and "Migrar para a versão vigente" in page
    client.post(
        reverse("subdocuments:migrate", args=[formulation.pk]), {"motivo": "Versão 06 vigente"}
    )
    formulation.refresh_from_db()
    assert formulation.template.form_version == 6


@pytest.mark.req("004:FR-019")
def test_atualizar_derivados_pela_tela(
    client, project, approved_entry, analyst, make_subdocument, approve_quick
):
    for code in ("formulacao", "lote-piloto", "rapd", "analise-critica", "validacao"):
        approve_quick(make_subdocument(project, code))
    final = make_subdocument(project, "verificacao-final")
    client.force_login(analyst)
    edit_url = reverse("subdocuments:edit", args=[final.pk])
    page = client.get(edit_url).content.decode()
    assert (
        "Requisitos de entrada" in page and "Previsto" in page and "Tipos de amostra: Soro" in page
    )
    response = client.post(
        edit_url,
        {
            "row_version": final.row_version,
            "t__checklist__requisitos__0__realizado": "Soro testado",
            "t__checklist__requisitos__0__disposicao": "aprovado",
            "t__checklist__requisitos__0__justificativa": "",
        },
    )
    assert response.status_code == 302
    client.post(reverse("subdocuments:refresh", args=[final.pk]))
    final.refresh_from_db()
    row = final.topic_data("checklist")["values"]["requisitos"]["rows"][0]
    assert row["values"]["realizado"] == "Soro testado"


@pytest.mark.req("004:FR-013")
def test_busca_de_cadastro_em_modo_de_selecao(client, project, analyst, make_material):
    make_material(analyst, code="MP-SEL-1", new_to_company=True, material_type="raw")
    make_material(analyst, code="MP-SEL-2", new_to_company=False, material_type="raw")
    client.force_login(analyst)
    fragment = client.get(
        reverse("catalog:search", args=["insumos"]),
        {"q": "MP-SEL", "campo": "t__x__y", "tipo_insumo": "raw", "novo": "1"},
    ).content.decode()
    assert 'name="t__x__y"' in fragment and "MP-SEL-1" in fragment and "MP-SEL-2" not in fragment
