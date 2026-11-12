"""Linha do tempo, pendências e exportação (FR-003, FR-005, FR-006)."""

import io

import pytest
from django.urls import reverse
from openpyxl import load_workbook

from sgp.dashboard import pending, timeline


@pytest.mark.req("010:FR-003")
def test_linha_do_tempo_em_ordem_por_categoria(
    client, project, analyst, manager, make_subdocument, make_user
):
    from sgp.accounts.profiles import Profile
    from sgp.notebook import services as notebook

    make_subdocument(project, "entrada")
    notebook.create_entry(project, by=analyst, data={"title": "Ensaio da linha do tempo"})
    events = list(timeline.events(manager, project))
    assert events == sorted(events, key=lambda e: -e.seq)
    types = {event.event_type for event in events}
    assert "notebook.created" in types and "subdocuments.created" in types
    notebook_only = {e.event_type for e in timeline.events(manager, project, "caderno")}
    assert notebook_only == {"notebook.created"}
    member_types = {e.event_type for e in timeline.events(analyst, project)}
    assert "projects.business_plan_updated" not in member_types
    assert {"projects.submitted", "projects.approved", "projects.milestone_added"} <= types
    client.force_login(analyst)
    page = client.get(reverse("dashboard:timeline", args=[project.pk]))
    assert page.status_code == 200 and "Ensaio da linha do tempo" in page.content.decode()
    client.force_login(make_user(None, Profile.ANALYST))
    assert client.get(reverse("dashboard:timeline", args=[project.pk])).status_code == 403


@pytest.mark.req("010:FR-005")
def test_minhas_pendencias(client, project, analyst, manager, submitted_entry, signing):
    from sgp.notebook import services as notebook
    from sgp.signatures import services as signatures

    sub = submitted_entry
    assert [row["obj"].pk for row in pending.my_pending(manager)["approvals"]] == [sub.pk]
    signatures.return_document("subdocument", sub, by=manager, comment="Faltou o tópico 3")
    mine = pending.my_pending(analyst)
    assert [item.pk for item in mine["returned"]] == [sub.pk]
    entry = notebook.create_entry(
        project, by=analyst, data={"title": "Assinar depois", "relevant": True}
    )
    assert [item["entry"].pk for item in pending.my_pending(analyst)["entries"]] == [entry.pk]
    notebook.sign_entry(entry, by=analyst, password=signing.password)
    assert [item.pk for item in pending.my_pending(project.leader)["witness"]] == [entry.pk]
    client.force_login(analyst)
    page = client.get(reverse("dashboard:pending")).content.decode()
    assert "Devolvidos para você corrigir" in page


@pytest.mark.req("010:FR-006")
def test_exportacao_com_as_permissoes_do_painel(client, project, analyst, manager, events):
    client.force_login(manager)
    response = client.get(reverse("dashboard:export"))
    sheet = load_workbook(io.BytesIO(response.content)).active
    header = [cell.value for cell in sheet[1]]
    assert header[:5] == ["Projeto", "Título", "Produto", "Líder", "Etapa atual"]
    assert "Custo planejado" in header
    assert any(row[0] == project.code for row in sheet.iter_rows(min_row=2, values_only=True))
    client.force_login(analyst)
    member_sheet = load_workbook(io.BytesIO(client.get(reverse("dashboard:export")).content)).active
    assert "Custo planejado" not in [cell.value for cell in member_sheet[1]]
    exported = events("dashboard.exported")
    assert len(exported) == 2 and exported[0].new_value["com_dados_financeiros"] is True
