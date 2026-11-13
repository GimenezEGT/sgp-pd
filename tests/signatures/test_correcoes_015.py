"""Correções do ciclo de revisão e assinatura (feature 015): revisão única por pessoa e versão,
Gestor que elaborou (aviso, devolução, fila e envio) e situação pelo nome."""

from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from sgp.signatures import services
from sgp.signatures.models import Signature
from sgp.subdocuments.models import Subdocument

pytestmark = [pytest.mark.django_db]
KIND = "subdocument"
OWN_WARNING = "Você assinou esta versão como Elaborado"
SUBMIT_WARNING = "não poderá aprovar esta versão"


def _page(client, user, url):
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    return response.content.decode()


def _reviews(obj, user):
    return Signature.objects.filter(
        kind=KIND, object_id=obj.pk, meaning="reviewed", signer=user, version=obj.version
    ).count()


@pytest.mark.req("015:FR-005")
@pytest.mark.req("015:SC-001")
def test_revisao_unica_por_pessoa_e_versao(
    complete_formulation, analyst, manager, project, signing
):
    reviewer = project.leader
    signing.enable(reviewer)
    signing.submit(KIND, complete_formulation, analyst)
    complete_formulation.refresh_from_db()
    services.sign_review(KIND, complete_formulation, by=reviewer, password=signing.password)
    assert services.block_context(reviewer, KIND, complete_formulation)["can_review"] is False
    with pytest.raises(ValidationError, match="Você já assinou como revisor esta versão."):
        services.sign_review(KIND, complete_formulation, by=reviewer, password=signing.password)
    assert _reviews(complete_formulation, reviewer) == 1
    signing.approve(KIND, complete_formulation, manager)
    services.new_version(KIND, complete_formulation, by=analyst, reason="Ajuste do preparo")
    second = Subdocument.objects.get(pk=complete_formulation.pk)
    signing.submit(KIND, second, analyst)
    second.refresh_from_db()
    assert services.block_context(reviewer, KIND, second)["can_review"] is True
    services.sign_review(KIND, second, by=reviewer, password=signing.password)
    assert _reviews(second, reviewer) == 1 and second.version == 2


@pytest.mark.req("015:FR-001")
@pytest.mark.req("015:FR-002")
@pytest.mark.req("015:FR-007")
@pytest.mark.req("015:SC-002")
def test_gestor_que_elaborou_ve_aviso_e_devolve(
    client, complete_formulation, analyst, manager, signing, events
):
    signing.submit(KIND, complete_formulation, manager)
    complete_formulation.refresh_from_db()
    url = reverse("subdocuments:detail", args=[complete_formulation.pk])
    page = _page(client, manager, url)
    assert OWN_WARNING in page and reverse("signatures:delegations") in page
    assert reverse("signatures:return", args=[KIND, complete_formulation.pk]) in page
    assert "Aprovar ou devolver" not in page
    response = client.post(
        reverse("signatures:return", args=[KIND, complete_formulation.pk]), {"comentario": " "}
    )
    assert Subdocument.objects.get(pk=complete_formulation.pk).status == "in_review"
    response = client.post(
        reverse("signatures:return", args=[KIND, complete_formulation.pk]),
        {"comentario": "Enviado pelo perfil errado; reenviar pela analista."},
    )
    assert response.status_code == 302
    assert Subdocument.objects.get(pk=complete_formulation.pk).status == "returned"
    assert events("signatures.returned")
    analyst_page = _page(client, analyst, url)
    assert OWN_WARNING not in analyst_page


@pytest.mark.req("015:FR-001")
@pytest.mark.req("015:FR-002")
def test_analista_que_elaborou_nao_ve_devolucao(client, complete_formulation, analyst, signing):
    signing.submit(KIND, complete_formulation, analyst)
    complete_formulation.refresh_from_db()
    page = _page(client, analyst, reverse("subdocuments:detail", args=[complete_formulation.pk]))
    assert OWN_WARNING not in page
    assert reverse("signatures:return", args=[KIND, complete_formulation.pk]) not in page


@pytest.mark.req("015:FR-003")
@pytest.mark.req("015:SC-002")
def test_fila_mostra_os_elaborados_pela_pessoa_a_parte(
    client, complete_formulation, manager, signing
):
    signing.submit(KIND, complete_formulation, manager)
    complete_formulation.refresh_from_db()
    assert services.review_queue(manager) == []
    own = services.review_queue(manager, own=True)
    assert [row["obj"].pk for row in own] == [complete_formulation.pk]
    page = _page(client, manager, reverse("signatures:queue"))
    assert "Elaborados por você" in page
    assert reverse("subdocuments:detail", args=[complete_formulation.pk]) in page
    assert reverse("signatures:approve", args=[KIND, complete_formulation.pk]) not in page


@pytest.mark.req("015:FR-004")
def test_envio_avisa_quem_pode_aprovar(client, complete_formulation, analyst, manager):
    url = reverse("signatures:submit", args=[KIND, complete_formulation.pk])
    assert SUBMIT_WARNING in _page(client, manager, url)
    assert SUBMIT_WARNING not in _page(client, analyst, url)


@pytest.mark.req("015:FR-004")
@pytest.mark.req("015:FR-007")
def test_aprovacao_pelo_endereco_direto_por_quem_elaborou(
    client, complete_formulation, manager, signing
):
    signing.submit(KIND, complete_formulation, manager)
    complete_formulation.refresh_from_db()
    url = reverse("signatures:approve", args=[KIND, complete_formulation.pk])
    page = _page(client, manager, url)
    assert "Aprovar e assinar" not in page and OWN_WARNING in page and "Devolver" in page
    response = client.post(url, {"senha": signing.password}, follow=True)
    assert "Quem elaborou não pode aprovar o mesmo documento." in response.content.decode()
    assert Subdocument.objects.get(pk=complete_formulation.pk).status == "in_review"


@pytest.mark.req("015:FR-001")
@pytest.mark.req("015:FR-007")
def test_delegado_que_elaborou_nao_aprova_e_nao_ve_delegacoes(
    client, complete_formulation, manager, project, signing
):
    leader = project.leader
    today = timezone.localdate()
    services.create_delegation(
        by=manager,
        delegate=leader,
        starts_on=today,
        ends_on=today + timedelta(days=5),
        reason="Férias do Gestor",
    )
    signing.submit(KIND, complete_formulation, leader)
    complete_formulation.refresh_from_db()
    context = services.block_context(leader, KIND, complete_formulation)
    assert context["can_approve"] is False and context["own_submission"] is True
    assert context["can_return_own"] is True
    page = _page(client, leader, reverse("subdocuments:detail", args=[complete_formulation.pk]))
    assert OWN_WARNING in page and reverse("signatures:delegations") not in page
    with pytest.raises(ValidationError, match="Quem elaborou não pode aprovar"):
        signing.approve(KIND, complete_formulation, leader)


@pytest.mark.req("015:FR-006")
@pytest.mark.req("015:SC-003")
def test_situacao_pelo_nome_nas_telas(client, complete_formulation, analyst, manager, signing):
    submit_page = _page(
        client, analyst, reverse("signatures:submit", args=[KIND, complete_formulation.pk])
    )
    assert "situação Rascunho" in submit_page and "situação draft" not in submit_page
    signing.submit(KIND, complete_formulation, analyst)
    complete_formulation.refresh_from_db()
    approve_page = _page(
        client, manager, reverse("signatures:approve", args=[KIND, complete_formulation.pk])
    )
    assert "situação Em revisão" in approve_page and "in_review" not in approve_page
