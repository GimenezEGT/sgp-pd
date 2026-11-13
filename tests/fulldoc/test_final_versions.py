"""Versões do documento final do projeto (feature 016): nascem com as aprovações das partes,
guardam mudança e composição, aparecem no documento gerado e nas telas e são reconstruídas a partir
das aprovações registradas."""

from datetime import timedelta

import pytest
from django.apps import apps as django_apps
from django.db import DatabaseError, connection, transaction
from django.urls import reverse
from django.utils import timezone

from sgp.fulldoc import compose, history, versioning
from sgp.fulldoc.models import FinalDocumentVersion
from sgp.signatures.models import ApprovedVersion
from tests.fulldoc.conftest import pdf_text
from tests.subdocuments.conftest import entry_topics, standard  # noqa: F401

pytestmark = [pytest.mark.django_db]


def _versions(project):
    return list(FinalDocumentVersion.objects.filter(project=project).order_by("number"))


@pytest.fixture
def entry(signed_project, member, standard):  # noqa: F811
    from sgp.subdocuments import services
    from sgp.vocab.models import get_term

    sub = services.create_subdocument(
        signed_project, get_term("tipo-subdocumento", "entrada"), by=member
    )
    return services.save_subdocument(sub, by=member, data={"topics": entry_topics(standard.pk)})


@pytest.mark.req("016:FR-002")
@pytest.mark.req("016:FR-004")
@pytest.mark.req("016:FR-005")
def test_aprovacao_do_projeto_gera_a_versao_01(signed_project, events):
    (version,) = _versions(signed_project)
    assert version.number == 1 and version.reason == "approval"
    assert {c["tipo"] for c in version.changes} == {"charter", "business_plan"}
    assert all(c["de"] is None and c["para"] == 1 for c in version.changes)
    assert [p["parte"] for p in version.composition] == [
        "Termo de Abertura do Projeto",
        "Plano de Negócios",
    ]
    assert all(len(p["resumo"]) == 64 and p["aprovada_em"] for p in version.composition)
    assert version.composition_hash == versioning.digest(version.composition)
    event = events("fulldoc.version_created")[-1]
    assert event.new_value["versao"] == 1 and event.new_value["partes"] == 2


@pytest.mark.req("016:FR-001")
@pytest.mark.req("016:FR-003")
@pytest.mark.req("016:SC-001")
def test_aprovacao_de_parte_sobe_a_versao_e_rascunho_nao(
    signed_project, entry, member, manager, signing, events
):
    from sgp.signatures import services as signatures

    signing.submit("subdocument", entry, member)
    entry.refresh_from_db()
    assert len(_versions(signed_project)) == 1
    signing.approve("subdocument", entry, manager)
    second = _versions(signed_project)[-1]
    assert second.number == 2 and second.registered_by == manager
    assert second.changes_text == "Entrada de Projeto: — → 01"
    assert len(second.composition) == 3
    signatures.new_version("subdocument", entry, by=member, reason="Ajuste fictício do escopo")
    entry.refresh_from_db()
    signing.submit("subdocument", entry, member)
    entry.refresh_from_db()
    signatures.return_document("subdocument", entry, by=manager, comment="Detalhar o escopo")
    entry.refresh_from_db()
    assert len(_versions(signed_project)) == 2
    signing.submit("subdocument", entry, member)
    entry.refresh_from_db()
    signing.approve("subdocument", entry, manager)
    third = _versions(signed_project)[-1]
    assert [v.number for v in _versions(signed_project)] == [1, 2, 3]
    assert third.changes_text == "Entrada de Projeto: 01 → 02"
    entrada = next(p for p in third.composition if p["tipo"] == "subdocument")
    charter = next(p for p in third.composition if p["tipo"] == "charter")
    assert entrada["versao"] == 2 and charter["versao"] == 1
    assert len(events("fulldoc.version_created")) == 3


@pytest.mark.req("016:FR-003")
def test_alteracao_de_projeto_tambem_gera_versao(
    signed_project, manager, create_sub, force_approve
):
    force_approve(create_sub(signed_project, "entrada"))
    change = create_sub(signed_project, "alteracao")
    force_approve(change)
    approval = ApprovedVersion.objects.get(kind="subdocument", object_id=change.pk)
    version = versioning.register(signed_project, by=manager, approvals=[approval])
    assert version.number == 2 and version.changes_text == "Alteração de Projeto 1: — → 01"
    assert [p["parte"] for p in version.composition][-1] == "Alteração de Projeto 1"


@pytest.mark.req("016:FR-004")
def test_versao_do_documento_final_e_imutavel(signed_project):
    (version,) = _versions(signed_project)
    with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cursor:
        cursor.execute(
            "UPDATE fulldoc_finaldocumentversion SET reason = 'approval' WHERE id = %s",
            [version.pk],
        )


@pytest.mark.req("016:FR-007")
@pytest.mark.req("016:FR-010")
@pytest.mark.req("016:SC-002")
def test_documento_gerado_traz_a_versao_e_o_quadro(
    client, complete_project, run_fulldoc, seal_cert, document_bytes
):
    project = complete_project()
    assert len(_versions(project)) == 1
    request = run_fulldoc(project, project.leader)
    document = request.result
    latest = _versions(project)[-1]
    assert latest.number == 2 and latest.reason == "recomposition"
    assert len(latest.changes) == 8 and document.final_version == latest
    assert document.file.original_name.endswith("v02.pdf")
    text = " ".join(pdf_text(document_bytes(document)))
    assert "VERSÃO DO DOCUMENTO FINAL" in text and "VERSÃO DO PROJETO" in text
    assert "Versões do documento final" in text and "Recomposição" in text
    assert "versão 02 do documento final" in str(document)
    again = run_fulldoc(project, project.leader)
    assert again.result == document and len(_versions(project)) == 2
    client.force_login(project.leader)
    page = client.get(reverse("documents:verify"), {"codigo": document.verification_code})
    assert (
        f"02 do documento final (projeto {document.project_version:02d})" in page.content.decode()
    )


@pytest.mark.req("016:FR-007")
def test_resumo_de_reaproveitamento_inclui_a_versao(signed_project, make_project):
    composition = {"parts": [], "final_number": 1, "options": {}, "with_financials": False}
    first = compose.composition_digest(signed_project, composition, layout_id=1, pending=[])
    composition["final_number"] = 2
    assert compose.composition_digest(signed_project, composition, layout_id=1, pending=[]) != first
    draft = make_project(title="Projeto sem aprovação")
    assert versioning.ensure_current(draft, by=draft.leader) is None
    assert compose.final_version_rows(draft, None) == []


@pytest.mark.req("016:FR-006")
@pytest.mark.req("016:SC-003")
def test_tela_do_projeto_mostra_o_historico(client, signed_project, manager):
    from sgp.dashboard import timeline

    on_timeline = timeline.events(manager, signed_project, "documentos")
    assert [e.event_type for e in on_timeline].count("fulldoc.version_created") == 1
    client.force_login(manager)
    page = client.get(reverse("fulldoc:project", args=[signed_project.pk])).content.decode()
    assert "Versões do documento final" in page and "Versão do documento final" in page
    assert "Termo de Abertura do Projeto – versão 01" in page
    assert "Plano de Negócios – versão 01" in page and "Aprovação" in page


@pytest.mark.req("016:FR-008")
def test_historico_de_versoes_da_parte(client, signed_project, entry, member, manager, signing):
    from sgp.signatures import services as signatures

    signing.submit("subdocument", entry, member)
    entry.refresh_from_db()
    signing.approve("subdocument", entry, manager)
    signatures.new_version("subdocument", entry, by=member, reason="Ajuste fictício do escopo")
    entry.refresh_from_db()
    rows = versioning.part_history("subdocument", entry)
    assert [(r["number"], r["situation"]) for r in rows] == [("01", "Vigente"), ("02", "Rascunho")]
    assert rows[0]["finals"] == ["02"] and rows[1]["finals"] == []
    assert rows[1]["reason"] == "Ajuste fictício do escopo" and rows[0]["reason"] == "Criação"
    client.force_login(member)
    page = client.get(reverse("subdocuments:detail", args=[entry.pk])).content.decode()
    assert "Histórico de versões" in page and "Ajuste fictício do escopo" in page


@pytest.mark.req("016:FR-008")
def test_historico_do_tap_e_do_plano_na_tela_do_projeto(client, signed_project, manager):
    client.force_login(manager)
    page = client.get(reverse("projects:detail", args=[signed_project.pk])).content.decode()
    assert page.count("Histórico de versões") >= 2 and "Vigente" in page
    assert "Criação" in page


@pytest.mark.req("016:FR-009")
def test_reconstrucao_a_partir_das_aprovacoes(open_project, manager):
    from sgp.subdocuments import services
    from sgp.vocab.models import get_term

    project = open_project()
    leader = project.leader
    entrada = services.create_subdocument(
        project, get_term("tipo-subdocumento", "entrada"), by=leader
    )
    start = timezone.now() - timedelta(days=10)

    def approve(kind, object_id, version, moment):
        ApprovedVersion.objects.create(
            kind=kind,
            object_id=object_id,
            project=project,
            version=version,
            content={},
            content_hash=f"{kind}{object_id}{version}".ljust(64, "0")[:64],
            approved_by=manager,
            approved_at=moment,
        )

    approve("charter", project.charter.pk, 1, start)
    approve("business_plan", project.business_plan.pk, 1, start + timedelta(seconds=1))
    approve("subdocument", entrada.pk, 1, start + timedelta(hours=1))
    formulacao = services.create_subdocument(
        project, get_term("tipo-subdocumento", "formulacao"), by=leader
    )
    approve("subdocument", formulacao.pk, 1, start + timedelta(hours=2))
    approve("subdocument", entrada.pk, 2, start + timedelta(hours=3))
    assert history.rebuild(django_apps) >= 4
    versions = _versions(project)
    assert [v.number for v in versions] == [1, 2, 3, 4]
    assert all(v.reason == "reconstruction" for v in versions)
    assert [len(v.composition) for v in versions] == [2, 3, 4, 4]
    assert versions[0].created_at == start and len(versions[0].changes) == 2
    assert versions[3].changes_text == "Entrada de Projeto: 01 → 02"
    assert [p["parte"] for p in versions[3].composition][:3] == [
        "Termo de Abertura do Projeto",
        "Plano de Negócios",
        "Entrada de Projeto",
    ]
    assert versioning.ensure_current(project, by=manager) == versions[3]
    assert history.rebuild(django_apps) == 0


@pytest.mark.req("016:FR-005")
@pytest.mark.req("016:FR-009")
def test_versoes_reconstruidas_entram_na_trilha(open_project, manager, events):
    from sgp.audit.services import SYSTEM_ACTOR
    from sgp.fulldoc.apps import record_reconstruction_events

    project = open_project()
    moment = timezone.now() - timedelta(days=3)
    for kind, obj in (("charter", project.charter), ("business_plan", project.business_plan)):
        ApprovedVersion.objects.create(
            kind=kind,
            object_id=obj.pk,
            project=project,
            version=1,
            content={},
            content_hash=kind.ljust(64, "0"),
            approved_by=manager,
            approved_at=moment,
        )
    assert history.rebuild(django_apps) == 1
    assert events("fulldoc.version_created") == []
    assert record_reconstruction_events(sender=None) == 1
    (event,) = events("fulldoc.version_created")
    (version,) = _versions(project)
    assert event.object_id == str(version.pk) and event.actor_id is None
    assert event.actor_username == SYSTEM_ACTOR and event.reason == history.TRAIL_NOTE
    assert event.new_value["motivo"] == "reconstruction" and event.new_value["versao"] == 1
    assert event.new_value["aprovada_por"] == manager.username
    assert event.new_value["aprovada_em"] == moment.isoformat()
    assert event.occurred_at > moment
    assert record_reconstruction_events(sender=None) == 0
    assert record_reconstruction_events(sender=None, using="outro") == 0
