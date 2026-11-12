"""Integridade, delegação, fila e assinaturas do projeto (FR-010 a FR-014, SC-001, SC-005)."""

import time
from datetime import timedelta
from pathlib import Path

import pytest
from django.core.exceptions import ValidationError
from django.db import ProgrammingError
from django.urls import reverse
from django.utils import timezone

from sgp.accounts.profiles import Profile
from sgp.signatures import services
from sgp.signatures.models import ApprovedVersion, Signature
from sgp.subdocuments.models import Subdocument
from tests.db_helpers import app_role_exists, run_as_app_role, tamper

pytestmark = [pytest.mark.django_db]
KIND = "subdocument"


@pytest.fixture
def approved_formulation(complete_formulation, analyst, manager, signing):
    signing.submit_and_approve(KIND, complete_formulation, analyst, manager)
    return Subdocument.objects.get(pk=complete_formulation.pk)


@pytest.mark.req("005:FR-011")
def test_documento_integro(approved_formulation, analyst, events):
    result = services.verify(KIND, approved_formulation, by=analyst)
    assert result == {"integro": True, "problemas": [], "versoes": 1}
    assert events("signatures.verified")[-1].new_value["integro"] is True


@pytest.mark.req("005:FR-010")
@pytest.mark.req("005:FR-011")
@pytest.mark.req("005:SC-001")
def test_alteracao_no_banco_da_versao_aprovada_e_apontada(approved_formulation, analyst):
    version = ApprovedVersion.objects.get(kind=KIND, object_id=approved_formulation.pk)
    tamper(
        "UPDATE signatures_approvedversion SET content = jsonb_set(content, '{numero}', '99') WHERE id = %s",
        [version.pk],
        table="signatures_approvedversion",
        trigger="signatures_approvedversion_immutable",
    )
    result = services.verify(KIND, approved_formulation, by=analyst)
    assert result["integro"] is False
    assert any("não confere com o resumo aprovado" in problem for problem in result["problemas"])


@pytest.mark.req("005:FR-011")
def test_conteudo_atual_diferente_do_aprovado_e_apontado(approved_formulation, analyst):
    data = dict(approved_formulation.data)
    data["topics"]["modo_preparo"]["values"]["passos"] = "Alterado por fora"
    Subdocument.objects.filter(pk=approved_formulation.pk).update(data=data)
    result = services.verify(KIND, approved_formulation, by=analyst)
    assert "O conteúdo atual do documento difere da versão aprovada." in result["problemas"]


@pytest.mark.req("005:FR-011")
def test_anexo_alterado_e_apontado(
    project, analyst, manager, standard, make_subdocument, signing, settings
):
    from django.core.files.uploadedfile import SimpleUploadedFile

    from sgp.files.storage import store_upload
    from sgp.subdocuments import services as subdocument_services
    from tests.subdocuments.conftest import entry_topics

    entry = make_subdocument(project, "entrada")
    stored = store_upload(SimpleUploadedFile("matriz.pdf", b"%PDF-1.4\nmatriz\n%%EOF"), by=analyst)
    topics = entry_topics(standard.pk)
    topics["gerenciamento_risco"]["values"]["matriz"] = [stored.pk]
    subdocument_services.save_subdocument(entry, by=analyst, data={"topics": topics})
    signing.submit_and_approve(KIND, entry, analyst, manager)
    (Path(settings.MEDIA_ROOT) / stored.storage_name).write_bytes(b"%PDF-1.4 adulterado")
    result = services.verify(KIND, entry, by=analyst)
    assert any("anexo matriz.pdf alterado" in problem for problem in result["problemas"])


@pytest.mark.req("005:FR-010")
def test_papel_da_aplicacao_nao_altera_versoes_nem_assinaturas(approved_formulation):
    if not app_role_exists():
        pytest.skip("Papel da aplicação inexistente neste banco.")
    version = ApprovedVersion.objects.get(kind=KIND, object_id=approved_formulation.pk)
    signature = Signature.objects.filter(object_id=approved_formulation.pk).first()
    with pytest.raises(ProgrammingError, match="permission denied"):
        run_as_app_role(
            "UPDATE signatures_approvedversion SET content_hash = 'x' WHERE id = %s", [version.pk]
        )
    with pytest.raises(ProgrammingError, match="permission denied"):
        run_as_app_role("DELETE FROM signatures_signature WHERE id = %s", [signature.pk])


@pytest.mark.req("005:SC-005")
def test_verificacao_de_10_versoes_em_menos_de_2_segundos(
    approved_formulation, analyst, manager, signing
):
    formulation = approved_formulation
    for index in range(9):
        services.new_version(KIND, formulation, by=analyst, reason=f"Revisão {index}")
        signing.submit_and_approve(KIND, formulation, analyst, manager)
        formulation = Subdocument.objects.get(pk=formulation.pk)
    start = time.monotonic()
    result = services.verify(KIND, formulation, by=analyst)
    elapsed = time.monotonic() - start
    assert result["integro"] and result["versoes"] == 10
    assert elapsed < 2, f"verificação levou {elapsed:.2f} s"


@pytest.mark.req("005:FR-013")
def test_delegacao_de_aprovacao(
    complete_formulation, analyst, manager, make_user, signing, project
):
    from sgp.projects import services as project_services

    delegate = make_user(None, Profile.QUALITY)
    project_services.add_member(project, by=project.leader, user=delegate, role="Qualidade")
    today = timezone.localdate()
    with pytest.raises(ValidationError, match="motivo"):
        services.create_delegation(
            by=manager, delegate=delegate, starts_on=today, ends_on=today, reason=""
        )
    with pytest.raises(ValidationError, match="até 30 dias"):
        services.create_delegation(
            by=manager,
            delegate=delegate,
            starts_on=today,
            ends_on=today + timedelta(days=30),
            reason="Férias",
        )
    with pytest.raises(ValidationError, match="perfil"):
        services.create_delegation(
            by=manager,
            delegate=make_user(None, Profile.READER),
            starts_on=today,
            ends_on=today,
            reason="x",
        )
    delegation = services.create_delegation(
        by=manager,
        delegate=delegate,
        starts_on=today,
        ends_on=today + timedelta(days=6),
        reason="Férias do Gestor",
    )
    signing.submit(KIND, complete_formulation, analyst)
    signing.approve(KIND, complete_formulation, delegate)
    approved = Signature.objects.get(object_id=complete_formulation.pk, meaning="approved")
    assert approved.delegation == delegation and approved.signer == delegate
    services.end_delegation(delegation, by=manager, reason="Gestor voltou")
    assert services.active_delegation(delegate) is None
    assert not services.is_approver(delegate)


@pytest.mark.req("005:FR-013")
def test_delegacao_vencida_nao_aprova(complete_formulation, analyst, manager, make_user, signing):
    delegate = make_user(None, Profile.PROJECT_LEADER)
    past = timezone.localdate() - timedelta(days=10)
    services.create_delegation(
        by=manager,
        delegate=delegate,
        starts_on=past,
        ends_on=past + timedelta(days=2),
        reason="Antiga",
    )
    signing.submit(KIND, complete_formulation, analyst)
    with pytest.raises(ValidationError, match="Só o Gestor"):
        signing.approve(KIND, complete_formulation, delegate)


@pytest.mark.req("005:FR-014")
def test_fila_com_atrasados(complete_formulation, analyst, manager, signing, settings):
    signing.submit(KIND, complete_formulation, analyst)
    rows = services.review_queue(manager)
    assert len(rows) == 1 and rows[0]["overdue"] is False
    old = timezone.now() - timedelta(days=settings.REVIEW_ALERT_DAYS + 2)
    tamper(
        "UPDATE signatures_signature SET signed_at = %s WHERE object_id = %s",
        [old, complete_formulation.pk],
        table="signatures_signature",
        trigger="signatures_signature_immutable",
    )
    rows = services.review_queue(manager)
    assert rows[0]["overdue"] is True and rows[0]["days"] >= settings.REVIEW_ALERT_DAYS + 2
    assert services.review_queue(analyst) == []


@pytest.mark.req("005:FR-012")
def test_projeto_assinado_no_tap_e_no_plano(client, make_project, fill_project, manager, signing):
    project = fill_project(make_project())
    signing.enable(project.leader, manager)
    client.force_login(project.leader)
    page = client.post(
        reverse("projects:submit", args=[project.pk]), {"senha": "errada"}, follow=True
    ).content.decode()
    assert "Senha de rede incorreta" in page
    client.post(reverse("projects:submit", args=[project.pk]), {"senha": signing.password})
    elaborated = Signature.objects.filter(project=project, meaning="elaborated")
    assert set(elaborated.values_list("kind", flat=True)) == {"charter", "business_plan"}
    client.force_login(manager)
    client.post(reverse("projects:approve", args=[project.pk]), {"senha": signing.password})
    project.refresh_from_db()
    assert project.status == "open"
    assert (
        project.charter.doc_status == "approved" and project.business_plan.doc_status == "approved"
    )
    assert ApprovedVersion.objects.filter(project=project).count() == 2
    assert services.verify("charter", project.charter, by=manager)["integro"] is True


@pytest.mark.req("005:FR-012")
def test_devolver_projeto_devolve_tap_e_plano_e_nova_versao_do_tap(
    make_project, fill_project, manager, signing, make_user
):
    project = fill_project(make_project())
    signing.enable(project.leader, manager)
    services.submit_project(project, by=project.leader, password=signing.password)
    services.return_project(project, by=manager, comment="Detalhar riscos")
    project.refresh_from_db()
    assert (
        project.charter.doc_status == "returned" and project.business_plan.doc_status == "returned"
    )
    services.submit_project(project, by=project.leader, password=signing.password)
    services.approve_project(project, by=manager, password=signing.password)
    project.refresh_from_db()
    charter = project.charter
    from sgp.projects import services as project_services

    with pytest.raises(ValidationError, match="crie uma nova versão"):
        project_services.update_charter(
            project, by=project.leader, data={"objective": "Novo objetivo"}
        )
    services.new_version("charter", charter, by=project.leader, reason="Ajuste do objetivo")
    project_services.update_charter(project, by=project.leader, data={"objective": "Novo objetivo"})
    services.submit("charter", charter, by=project.leader, password=signing.password)
    services.approve("charter", charter, by=manager, password=signing.password)
    charter.refresh_from_db()
    assert (charter.doc_version, charter.doc_status) == (2, "approved")
    versions = services.versions_of(services.get_adapter("charter"), charter)
    assert [item.superseded for item in versions] == [True, False]
