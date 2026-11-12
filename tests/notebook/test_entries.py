"""Entrada do caderno: criação, edição, materiais e anexos (FR-001 a FR-004, FR-014)."""

from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from sgp.notebook import services
from sgp.notebook.models import EntryStatus, MaterialKind, NotebookEntry

from .conftest import csv_file, png_file


@pytest.mark.req("008:FR-001")
def test_entrada_nasce_numerada_com_hora_do_servidor(
    make_entry, project, analyst, open_project, events
):
    before = timezone.now()
    first = make_entry(created_at=before - timedelta(days=30))
    second = make_entry("Segundo ensaio")
    assert (first.number, second.number) == (1, 2)
    assert first.author == analyst and first.status == EntryStatus.OPEN
    assert before <= first.created_at <= timezone.now()
    other = open_project()
    elsewhere = services.create_entry(other, by=other.leader, data={"title": "Outro projeto"})
    assert elsewhere.number == 1
    created = events("notebook.created")
    assert len(created) == 3 and created[0].new_value["numero"] == 1
    with pytest.raises(ValidationError, match="título"):
        make_entry("   ")


@pytest.mark.req("008:FR-004")
def test_so_editores_do_projeto_criam_entradas(
    project, analyst, manager, quality, outsider, make_user
):
    from sgp.accounts.profiles import Profile
    from sgp.projects import services as project_services

    reader = make_user(None, Profile.READER)
    project_services.add_member(project, by=project.leader, user=reader, role="Consulta")
    for person in (outsider, quality, reader):
        with pytest.raises(PermissionDenied):
            services.create_entry(project, by=person, data={"title": "Sem permissão"})
    assert services.create_entry(project, by=manager, data={"title": "Do gestor"}).number == 1
    assert services.create_entry(project, by=project.leader, data={"title": "Do líder"}).number == 2


@pytest.mark.req("008:FR-004")
@pytest.mark.req("008:FR-014")
def test_tentativa_sem_permissao_e_negada_e_registrada(
    client, project, outsider, make_entry, events
):
    entry = make_entry()
    client.force_login(outsider)
    assert client.get(reverse("notebook:detail", args=[entry.pk])).status_code == 403
    assert (
        client.post(reverse("notebook:create", args=[project.pk]), {"title": "x"}).status_code
        == 403
    )
    assert client.get(reverse("notebook:project", args=[project.pk])).status_code == 403
    assert len(events("auth.permission_denied")) == 3
    assert not NotebookEntry.objects.filter(title="x").exists()


@pytest.mark.req("008:FR-001")
@pytest.mark.req("008:FR-014")
def test_so_o_autor_edita_e_o_texto_e_sanitizado(make_entry, analyst, colleague, events):
    entry = make_entry()
    entry = services.update_entry(
        entry,
        by=analyst,
        data={"procedure": "<p>Pesar <b>2 g</b></p><script>x()</script>", "objective": "Avaliar"},
        row_version=entry.row_version,
    )
    assert entry.procedure == "<p>Pesar <b>2 g</b></p>"
    assert entry.objective == "<p>Avaliar</p>"
    assert "pesar 2 g" in entry.search_text
    updated = events("notebook.updated")[-1]
    assert set(updated.new_value) == {"procedimento", "objetivo"}
    with pytest.raises(PermissionDenied):
        services.update_entry(entry, by=colleague, data={"conclusion": "Alheio"})
    with pytest.raises(ValidationError, match="alterada por outra"):
        services.update_entry(entry, by=analyst, data={"conclusion": "x"}, row_version=1)


@pytest.mark.req("008:FR-002")
def test_materiais_pela_versao_do_cadastro(
    make_entry, analyst, project, make_lot, make_material, make_sample, open_project, events
):
    lot = make_lot(project, analyst, code="L-NB-1")
    material = make_material(analyst, code="MP-NB-1")
    sample = make_sample(analyst)
    entry = make_entry()
    item = services.add_material(entry, by=analyst, kind=MaterialKind.LOT, code="l-nb-1")
    assert (item.lot, item.code, item.version) == (lot, "L-NB-1", lot.version)
    services.add_material(entry, by=analyst, kind=MaterialKind.MATERIAL, code="MP-NB-1")
    services.add_material(entry, by=analyst, kind=MaterialKind.SAMPLE, code=sample.identifier)
    assert entry.materials.filter(removed_at__isnull=True).count() == 3
    assert material.code in NotebookEntry.objects.get(pk=entry.pk).search_text.upper()
    with pytest.raises(ValidationError, match="não existe no cadastro"):
        services.add_material(entry, by=analyst, kind=MaterialKind.LOT, code="L-INEXISTENTE")
    with pytest.raises(ValidationError, match="já está ligado"):
        services.add_material(entry, by=analyst, kind=MaterialKind.LOT, code="L-NB-1")
    other = open_project()
    make_lot(other, other.leader, code="L-OUTRO")
    with pytest.raises(ValidationError, match="deste projeto"):
        services.add_material(entry, by=analyst, kind=MaterialKind.LOT, code="L-OUTRO")
    services.remove_material(item, by=analyst)
    item.refresh_from_db()
    assert item.removed_at and item.removed_by == analyst
    assert len(events("notebook.material_added")) == 3
    assert len(events("notebook.material_removed")) == 1


@pytest.mark.req("008:FR-003")
def test_anexos_nos_tipos_e_no_limite_com_resumo(make_entry, analyst, settings, events):
    entry = make_entry()
    photo = services.add_attachment(entry, by=analyst, uploaded=png_file())
    sheet = services.add_attachment(entry, by=analyst, uploaded=csv_file())
    assert len(photo.file.sha256) == 64 and sheet.is_spreadsheet
    with pytest.raises(ValidationError, match="Tipo de arquivo"):
        services.add_attachment(
            entry, by=analyst, uploaded=SimpleUploadedFile("nota.txt", b"texto")
        )
    settings.FILE_MAX_MB = 1
    big = SimpleUploadedFile("grande.csv", b"1;2\n" * (300 * 1024), content_type="text/csv")
    with pytest.raises(ValidationError, match="máximo"):
        services.add_attachment(entry, by=analyst, uploaded=big)
    with pytest.raises(ValidationError, match="Tipo de arquivo"):
        services.add_attachment(entry, by=analyst, uploaded=csv_file(), inline=True)
    assert len(events("notebook.attachment_added")) == 2
    services.remove_attachment(sheet, by=analyst)
    assert entry.attachments.filter(removed_at__isnull=True).count() == 1


@pytest.mark.req("008:FR-003")
def test_imagem_colada_e_lida_com_conferencia_do_resumo(client, make_entry, analyst, outsider):
    from sgp.files.storage import media_root

    entry = make_entry()
    client.force_login(analyst)
    response = client.post(
        reverse("notebook:attachment_add", args=[entry.pk]),
        {"arquivo": png_file("colada.png"), "no_texto": "1"},
        HTTP_ACCEPT="application/json",
    )
    assert response.status_code == 200
    url = response.json()["url"]
    services.update_entry(entry, by=analyst, data={"results": f'<p><img src="{url}" alt="x"></p>'})
    entry.refresh_from_db()
    assert f'src="{url}"' in entry.results
    detail = client.get(reverse("notebook:detail", args=[entry.pk]))
    assert f'src="{url}"' in detail.content.decode()
    assert client.get(url).status_code == 200
    client.force_login(outsider)
    assert client.get(url).status_code == 403
    attachment = entry.attachments.get()
    (media_root() / attachment.file.storage_name).write_bytes(b"adulterado")
    client.force_login(analyst)
    assert client.get(url).status_code == 409
    bad = client.post(
        reverse("notebook:attachment_add", args=[entry.pk]),
        {"arquivo": SimpleUploadedFile("x.txt", b"x"), "no_texto": "1"},
        HTTP_ACCEPT="application/json",
    )
    assert bad.status_code == 400 and "erro" in bad.json()


@pytest.mark.req("008:FR-001")
def test_telas_de_criar_editar_e_ver(client, project, analyst):
    client.force_login(analyst)
    response = client.post(
        reverse("notebook:create", args=[project.pk]),
        {"title": "Ensaio pela tela", "relevant": "on"},
    )
    entry = NotebookEntry.objects.get(title="Ensaio pela tela")
    assert response.status_code == 302 and entry.relevant
    edit_url = reverse("notebook:edit", args=[entry.pk])
    page = client.get(edit_url)
    assert page.status_code == 200 and "notebook/editor.js" in page.content.decode()
    client.post(
        edit_url,
        {"title": "Ensaio pela tela", "row_version": entry.row_version, "conclusion": "Funcionou"},
    )
    entry.refresh_from_db()
    assert entry.conclusion == "<p>Funcionou</p>"
    detail = client.get(reverse("notebook:detail", args=[entry.pk])).content.decode()
    assert "Funcionou" in detail and "Assinar e bloquear" in detail
