"""Documentos do TAP e do Plano de Negócios (FR-023, FR-024)."""

import pytest
from django.core.exceptions import PermissionDenied
from django.urls import reverse

from sgp.accounts.profiles import Profile
from sgp.documents import content, layouts, seal, services
from tests.documents.conftest import flat, pdf_pages

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def signed_project(make_project, fill_project, manager, signing):
    from sgp.signatures import services as signatures

    project = fill_project(make_project())
    signing.enable(project.leader, manager)
    signatures.submit_project(project, by=project.leader, password=signing.password)
    signatures.approve_project(project, by=manager, password=signing.password)
    project.refresh_from_db()
    return project


@pytest.mark.req("006:FR-023")
def test_tap_em_rascunho_com_secoes_e_tabelas_numeradas(make_project, fill_project):
    project = fill_project(make_project())
    charter = project.charter
    data = content.build("charter", charter, layouts.layout_for("charter", charter.pk, 1))
    assert data["title"] == "Termo de Abertura de Projeto" and data["form_footer"] == ""
    labels = [section["label"] for section in data["sections"]]
    assert labels[:3] == ["Produto", "Justificativa", "Objetivo"]
    assert "Riscos iniciais" in labels and "Equipe" in labels
    tables = [
        b for s in data["sections"] for b in s["blocks"] if b["kind"] == "table" and b["rows"]
    ]
    assert tables[0]["number"] == "Tabela 01" and tables[0]["columns"] == [
        "Risco",
        "Impacto",
        "Resposta",
    ]


@pytest.mark.req("006:FR-023")
def test_tap_oficial_com_assinaturas_selo_codigo_e_rodape_do_layout(
    signed_project, generate, file_bytes, seal_cert
):
    charter = signed_project.charter
    doc = generate("charter", charter, "pdf", signed_project.leader).result
    assert doc.official and doc.verification_code and doc.form_template_id is None
    data = file_bytes(doc)
    assert seal.validate(data, [seal_cert])["intact"] is True
    cover = flat(pdf_pages(data)[0])
    assert "Termo de Abertura de Projeto" in cover
    assert "Elaborado (Nome/Função):" in cover and "Aprovado (Nome/Função):" in cover
    assert "assinatura eletrônica (Aprovado)" in cover
    assert "Formulário Versão" not in cover and "Página 1 de" in cover


@pytest.mark.req("006:FR-024")
def test_plano_de_negocios_so_para_quem_ve_dados_financeiros(
    signed_project, make_user, generate, client, events, seal_cert, file_bytes
):
    from sgp.projects import services as projects

    plan = signed_project.business_plan
    analyst = make_user(None, Profile.ANALYST)
    projects.add_member(signed_project, by=signed_project.leader, user=analyst, role="Analista")
    with pytest.raises(PermissionDenied):
        services.request_generation("business_plan", plan, "pdf", by=analyst)
    doc = generate("business_plan", plan, "pdf", signed_project.leader).result
    text = " ".join(flat(page) for page in pdf_pages(file_bytes(doc)))
    assert "Plano de Negócios" in text and "Retorno esperado (5 anos)" in text and "R$" in text
    client.force_login(analyst)
    assert client.get(reverse("documents:download", args=[doc.pk])).status_code == 403
    assert (
        client.get(reverse("documents:history", args=["business_plan", plan.pk])).status_code == 403
    )
    page = client.get(
        reverse("documents:verify"), {"codigo": doc.verification_code}
    ).content.decode()
    assert "Código válido" in page and "não tem acesso ao projeto" in page
    assert len(events("auth.permission_denied")) == 2
    client.force_login(signed_project.leader)
    assert client.get(reverse("documents:download", args=[doc.pk])).status_code == 200
