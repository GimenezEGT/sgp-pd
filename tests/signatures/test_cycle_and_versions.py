"""Ciclo de revisão, assinaturas e versões (US1 a US4: FR-001 a FR-005, FR-007, FR-009, SC-002, SC-003)."""

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from sgp.accounts.profiles import Profile
from sgp.signatures import services
from sgp.signatures.models import ApprovedVersion, ReviewComment, Signature
from sgp.subdocuments import services as subdocument_services
from sgp.subdocuments.models import Subdocument

pytestmark = [pytest.mark.django_db]
KIND = "subdocument"


@pytest.mark.req("005:FR-002")
@pytest.mark.req("005:FR-006")
def test_envio_assina_elaborado_e_bloqueia_edicao(complete_formulation, analyst, signing, events):
    signing.submit(KIND, complete_formulation, analyst)
    formulation = Subdocument.objects.get(pk=complete_formulation.pk)
    assert formulation.status == "in_review"
    signature = Signature.objects.get(kind=KIND, object_id=formulation.pk)
    assert signature.meaning == "elaborated" and signature.signer == analyst
    assert (
        signature.signer_name == analyst.get_full_name()
        and signature.signer_title == analyst.job_title
    )
    assert signature.version == 1 and len(signature.content_hash) == 64
    assert events("signatures.submitted")[-1].new_value["resumo"] == signature.content_hash
    with pytest.raises(ValidationError, match="em revisão ou aprovado"):
        subdocument_services.save_subdocument(formulation, by=analyst, data={"topics": {}})


@pytest.mark.req("005:FR-003")
@pytest.mark.req("005:FR-007")
def test_devolucao_e_reenvio_exigem_nova_assinatura(
    complete_formulation, analyst, manager, signing
):
    signing.submit(KIND, complete_formulation, analyst)
    with pytest.raises(ValidationError, match="comentário"):
        services.return_document(KIND, complete_formulation, by=manager, comment=" ")
    services.return_document(KIND, complete_formulation, by=manager, comment="Detalhar o preparo")
    formulation = Subdocument.objects.get(pk=complete_formulation.pk)
    assert formulation.status == "returned"
    assert ReviewComment.objects.get(object_id=formulation.pk).text == "Detalhar o preparo"
    first = Signature.objects.get(object_id=formulation.pk, meaning="elaborated")
    data = formulation.data["topics"]["modo_preparo"]
    data["values"]["passos"] = "Dissolver e filtrar"
    subdocument_services.save_subdocument(
        formulation, by=analyst, data={"topics": {"modo_preparo": data}}
    )
    signing.submit(KIND, formulation, analyst)
    second = (
        Signature.objects.filter(object_id=formulation.pk, meaning="elaborated")
        .order_by("-pk")
        .first()
    )
    assert second.content_hash != first.content_hash
    signing.approve(KIND, formulation, manager)
    approved = ApprovedVersion.objects.get(kind=KIND, object_id=formulation.pk)
    assert approved.content_hash == second.content_hash
    # A assinatura da primeira rodada (antes da devolução) não acusa divergência.
    assert services.verify(KIND, formulation, by=manager)["integro"] is True


@pytest.mark.req("005:FR-004")
@pytest.mark.req("005:SC-002")
def test_aprovacao_e_regras_do_aprovador(
    complete_formulation, analyst, manager, make_user, signing
):
    signing.submit(KIND, complete_formulation, analyst)
    with pytest.raises(ValidationError, match="Só o Gestor"):
        signing.approve(KIND, complete_formulation, make_user(None, Profile.QUALITY))
    signing.approve(KIND, complete_formulation, manager)
    formulation = Subdocument.objects.get(pk=complete_formulation.pk)
    assert formulation.status == "approved"
    meanings = list(
        Signature.objects.filter(object_id=formulation.pk).values_list("meaning", flat=True)
    )
    assert meanings == ["elaborated", "approved"]
    with pytest.raises(ValidationError, match="não está em revisão"):
        signing.approve(KIND, formulation, manager)


@pytest.mark.req("005:FR-009")
def test_assinatura_de_revisao_por_terceiro(
    complete_formulation, analyst, make_user, signing, project
):
    signing.submit(KIND, complete_formulation, analyst)
    quality = make_user(None, Profile.QUALITY)
    signing.enable(quality, analyst)
    services.sign_review(KIND, complete_formulation, by=quality, password=signing.password)
    assert Subdocument.objects.get(pk=complete_formulation.pk).status == "in_review"
    with pytest.raises(ValidationError, match="Quem elaborou não assina como revisor"):
        services.sign_review(KIND, complete_formulation, by=analyst, password=signing.password)
    assert (
        Signature.objects.filter(object_id=complete_formulation.pk, meaning="reviewed").count() == 1
    )


@pytest.mark.req("005:FR-005")
@pytest.mark.req("005:SC-003")
def test_nova_versao_e_versao_substituida_consultavel(
    client, complete_formulation, analyst, manager, signing, events
):
    signing.submit_and_approve(KIND, complete_formulation, analyst, manager)
    with pytest.raises(ValidationError, match="motivo"):
        services.new_version(KIND, complete_formulation, by=analyst, reason="")
    services.new_version(
        KIND, complete_formulation, by=analyst, reason="Correção do modo de preparo"
    )
    formulation = Subdocument.objects.get(pk=complete_formulation.pk)
    assert (formulation.version, formulation.status) == (2, "draft")
    assert events("signatures.new_version")[-1].reason == "Correção do modo de preparo"
    with pytest.raises(ValidationError, match="Só documento aprovado"):
        services.new_version(KIND, formulation, by=analyst, reason="De novo")
    signing.submit_and_approve(KIND, formulation, analyst, manager)
    versions = services.versions_of(
        services.get_adapter(KIND), Subdocument.objects.get(pk=formulation.pk)
    )
    assert [(item.version, item.superseded) for item in versions] == [(1, True), (2, False)]
    client.force_login(analyst)
    page = client.get(
        reverse("signatures:version", args=[KIND, formulation.pk, 1])
    ).content.decode()
    assert "versão 01 (Substituída)" in page and "Elaborado" in page and "Aprovado" in page
    detail = client.get(reverse("subdocuments:detail", args=[formulation.pk])).content.decode()
    assert "Assinaturas – versão 02" in detail and "Analista Responsável (Nome/Função):" in detail


@pytest.mark.req("005:FR-015")
def test_rotulo_do_aprovador_na_validacao(
    project, approved_entry, make_subdocument, approve_quick, client, analyst
):
    for code in ("formulacao", "lote-piloto", "rapd", "analise-critica"):
        approve_quick(make_subdocument(project, code))
    validation = make_subdocument(project, "validacao")
    from sgp.signatures.documents import get_adapter

    assert (
        get_adapter(KIND).approver_label(validation) == "Gestor de P&D responsável pela Aprovação:"
    )


@pytest.mark.req("005:FR-002")
def test_envio_pelas_telas(client, complete_formulation, analyst, manager, signing):
    signing.enable(analyst, manager)
    client.force_login(analyst)
    url = reverse("signatures:submit", args=[KIND, complete_formulation.pk])
    assert "Resumo do conteúdo que será assinado" in client.get(url).content.decode()
    page = client.post(url, {"senha": "errada"}, follow=True).content.decode()
    assert "Senha de rede incorreta" in page
    client.post(url, {"senha": signing.password})
    assert Subdocument.objects.get(pk=complete_formulation.pk).status == "in_review"
    client.force_login(manager)
    queue = client.get(reverse("signatures:queue")).content.decode()
    assert str(complete_formulation.subdocument_type.label) in queue
    client.post(
        reverse("signatures:approve", args=[KIND, complete_formulation.pk]),
        {"senha": signing.password},
    )
    assert Subdocument.objects.get(pk=complete_formulation.pk).status == "approved"


@pytest.mark.req("005:FR-001")
@pytest.mark.req("005:FR-016")
def test_ciclo_completo_passa_pelas_situacoes_e_gera_os_eventos(
    complete_formulation, analyst, manager, signing, events
):
    states = [Subdocument.objects.get(pk=complete_formulation.pk).status]
    signing.submit(KIND, complete_formulation, analyst)
    states.append(Subdocument.objects.get(pk=complete_formulation.pk).status)
    services.return_document(KIND, complete_formulation, by=manager, comment="Rever")
    states.append(Subdocument.objects.get(pk=complete_formulation.pk).status)
    signing.submit(KIND, complete_formulation, analyst)
    signing.approve(KIND, complete_formulation, manager)
    states.append(Subdocument.objects.get(pk=complete_formulation.pk).status)
    services.new_version(KIND, complete_formulation, by=analyst, reason="Correção")
    states.append(Subdocument.objects.get(pk=complete_formulation.pk).status)
    services.verify(KIND, complete_formulation, by=analyst)
    assert states == ["draft", "in_review", "returned", "approved", "draft"]
    versions = services.versions_of(
        services.get_adapter(KIND), Subdocument.objects.get(pk=complete_formulation.pk)
    )
    assert versions[0].superseded is True
    for event_type in (
        "signatures.submitted",
        "signatures.signed",
        "signatures.returned",
        "signatures.approved",
        "signatures.new_version",
        "signatures.verified",
    ):
        recorded = events(event_type)
        assert recorded, event_type
        assert recorded[-1].project_id == complete_formulation.project_id


@pytest.mark.req("005:FR-009")
def test_revisor_nao_aprova_a_mesma_versao(
    complete_formulation, analyst, manager, make_user, signing
):
    signing.submit(KIND, complete_formulation, analyst)
    signing.enable(manager)
    services.sign_review(KIND, complete_formulation, by=manager, password=signing.password)
    with pytest.raises(ValidationError, match="revisor não aprova"):
        signing.approve(KIND, complete_formulation, manager)
    other = make_user(None, Profile.RD_MANAGER)
    signing.approve(KIND, complete_formulation, other)
    assert Subdocument.objects.get(pk=complete_formulation.pk).status == "approved"
