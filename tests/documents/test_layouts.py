"""Modelos de layout mantidos pela Qualidade, versões, vínculo e imutabilidade (FR-019 a FR-022)."""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError, transaction
from django.urls import reverse
from django.utils import timezone

from sgp.accounts.profiles import Profile
from sgp.documents import layout_schema, layouts
from sgp.documents.models import GeneratedDocument, LayoutBinding, LayoutTemplate

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def seeded(vocab_seed):
    return layouts.current_layout("subdocument")


def _publish_new(quality, *, title_pt=30, valid_from=None):
    draft = LayoutTemplate.objects.filter(
        target="subdocument", status="draft"
    ).first() or layouts.create_draft("subdocument", by=quality)
    definition = draft.definition
    definition["cover"]["title_pt"] = title_pt
    draft = layouts.update_draft(
        draft,
        by=quality,
        definition=definition,
        valid_from=valid_from or timezone.localdate(),
        row_version=draft.row_version,
    )
    return layouts.publish(draft, by=quality)


@pytest.mark.req("006:FR-020")
def test_so_qualidade_cria_altera_e_publica(seeded, make_user, quality):
    analyst = make_user(None, Profile.ANALYST)
    with pytest.raises(ValidationError, match="Só a Qualidade/AR"):
        layouts.create_draft("subdocument", by=analyst)
    draft = layouts.create_draft("subdocument", by=quality)
    with pytest.raises(ValidationError, match="Só a Qualidade/AR"):
        layouts.update_draft(draft, by=analyst, definition=draft.definition)
    with pytest.raises(ValidationError, match="Só a Qualidade/AR"):
        layouts.publish(draft, by=analyst)


@pytest.mark.req("006:FR-020")
def test_telas_de_edicao_negadas_sem_perfil_e_registradas(seeded, client, login_as, events):
    login_as(Profile.ANALYST)
    for name in ("layouts:new_version", "layouts:publish"):
        assert client.post(reverse(name, args=[seeded.pk])).status_code == 403
    assert client.get(reverse("layouts:edit", args=[seeded.pk])).status_code == 403
    assert client.get(reverse("layouts:preview", args=[seeded.pk])).status_code == 403
    assert len(events("auth.permission_denied")) == 4
    assert client.get(reverse("layouts:detail", args=[seeded.pk])).status_code == 200
    assert client.get(reverse("layouts:list")).status_code == 200


@pytest.mark.req("006:FR-019")
def test_nova_versao_nasce_do_vigente_e_publicado_nao_muda(seeded, quality, events):
    draft = layouts.create_draft("subdocument", by=quality)
    assert (draft.version, draft.status) == (2, "draft")
    assert draft.definition == seeded.definition
    with pytest.raises(ValidationError, match="Já existe um rascunho"):
        layouts.create_draft("subdocument", by=quality)
    published = _publish_new(quality)
    assert published.status == "published" and published.definition["cover"]["title_pt"] == 30
    with pytest.raises(ValidationError, match="publicado não muda"):
        layouts.update_draft(published, by=quality, definition=published.definition)
    assert [e.event_type for e in events() if e.event_type.startswith("layouts.")] == [
        "layouts.draft_created",
        "layouts.draft_updated",
        "layouts.published",
    ]


@pytest.mark.req("006:FR-019")
def test_banco_recusa_alterar_layout_publicado(seeded):
    with pytest.raises(DatabaseError, match="publicado não pode ser alterado"):
        with transaction.atomic():
            LayoutTemplate.objects.filter(pk=seeded.pk).update(definition={})


@pytest.mark.req("006:FR-019")
def test_publicacao_recusa_definicao_invalida_e_vigencia_anterior(seeded, quality):
    draft = layouts.create_draft("subdocument", by=quality)
    definition = draft.definition
    definition["header"]["text"] = "{desconhecido}"
    draft = layouts.update_draft(draft, by=quality, definition=definition)
    with pytest.raises(ValidationError, match="marcador desconhecido"):
        layouts.publish(draft, by=quality)
    definition["header"]["text"] = "{titulo}"
    draft = layouts.update_draft(
        draft, by=quality, definition=definition, valid_from=datetime.date(2019, 1, 1)
    )
    with pytest.raises(ValidationError, match="anterior à da versão vigente"):
        layouts.publish(draft, by=quality)
    with pytest.raises(ValidationError):
        layouts.update_draft(draft, by=quality, definition={"page": {}})


@pytest.mark.req("006:FR-019")
def test_rascunho_desatualizado_e_recusado(seeded, quality):
    draft = layouts.create_draft("subdocument", by=quality)
    stale = draft.row_version
    layouts.update_draft(draft, by=quality, definition=draft.definition, row_version=stale)
    with pytest.raises(ValidationError, match="recarregue"):
        layouts.update_draft(draft, by=quality, definition=draft.definition, row_version=stale)


@pytest.mark.req("006:FR-021")
def test_documento_iniciado_fica_no_layout_e_o_novo_nasce_no_publicado(
    seeded, quality, project, approved_entry, make_subdocument
):
    first = make_subdocument(project, "formulacao")
    assert layouts.layout_for("subdocument", first.pk, 1) == seeded
    new_layout = _publish_new(quality)
    assert layouts.current_layout("subdocument") == new_layout
    assert layouts.layout_for("subdocument", first.pk, 1) == seeded
    second = make_subdocument(project, "alteracao")
    assert layouts.layout_for("subdocument", second.pk, 1) == new_layout


@pytest.mark.req("006:FR-021")
def test_nova_versao_do_documento_comeca_no_layout_vigente(
    seeded, quality, approved_entry, analyst
):
    from sgp.signatures import services

    new_layout = _publish_new(quality)
    services.new_version("subdocument", approved_entry, by=analyst, reason="Correção")
    assert layouts.layout_for("subdocument", approved_entry.pk, 1) == seeded
    assert layouts.layout_for("subdocument", approved_entry.pk, 2) == new_layout


@pytest.mark.req("006:FR-021")
def test_documento_sem_vinculo_usa_a_primeira_versao_publicada(seeded, quality, bare_project):
    _publish_new(quality)
    assert not LayoutBinding.objects.filter(kind="charter", object_id=999).exists()
    assert layouts.layout_for("charter", 999, 1) == layouts.first_layout("charter")
    assert LayoutBinding.objects.filter(kind="charter", object_id=999, version=1).exists()


@pytest.mark.req("006:FR-022")
def test_tap_e_plano_nascem_vinculados_aos_seus_layouts(seeded, make_project):
    project = make_project()
    assert layouts.layout_for("charter", project.charter.pk, 1).target == "charter"
    assert layouts.layout_for("business_plan", project.business_plan.pk, 1).target == (
        "business_plan"
    )


@pytest.mark.req("006:FR-019")
def test_formulario_de_edicao_grava_parametros_e_logotipo(seeded, client, quality, events):
    client.force_login(quality)
    client.post(reverse("layouts:new_version", args=[seeded.pk]))
    draft = LayoutTemplate.objects.get(status="draft")
    page = client.get(reverse("layouts:edit", args=[draft.pk]))
    assert page.status_code == 200
    data = {key: value for key, value in page.context["form"].initial.items() if value is not None}
    data.update({"cover_title_pt": "26", "title_pt__entrada": "22", "variant__saida": "sectors"})
    data["valid_from"] = timezone.localdate().isoformat()
    from sgp.documents.layouts import DEFAULT_LOGO

    data["logo"] = SimpleUploadedFile(
        "logo.png", DEFAULT_LOGO.read_bytes(), content_type="image/png"
    )
    response = client.post(reverse("layouts:edit", args=[draft.pk]), data)
    assert response.status_code == 302
    draft.refresh_from_db()
    assert draft.definition["cover"]["title_pt"] == 26
    assert draft.definition["cover"]["title_pt_by_type"]["entrada"] == 22
    assert draft.logo_id is not None
    assert layout_schema.validate_definition(draft.definition, target="subdocument") == []
    assert events("layouts.draft_updated")
    response = client.post(reverse("layouts:publish", args=[draft.pk]), {"observacao": "Teste"})
    draft.refresh_from_db()
    assert draft.status == "published" and draft.note == "Teste"
    logo = client.get(reverse("layouts:logo", args=[draft.pk]))
    assert logo.status_code == 200 and logo["Content-Type"] == "image/png"


@pytest.mark.req("006:FR-019")
def test_previa_gera_pdf_de_exemplo_sem_arquivar(seeded, client, quality):
    client.force_login(quality)
    response = client.get(reverse("layouts:preview", args=[seeded.pk]))
    assert response.status_code == 200 and response["Content-Type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")
    assert GeneratedDocument.objects.count() == 0
    charter = layouts.current_layout("charter")
    assert client.get(reverse("layouts:preview", args=[charter.pk])).status_code == 200


@pytest.mark.req("006:FR-025")
def test_logotipo_corrompido_faz_a_geracao_falhar_com_registro(
    seeded, quality, project, approved_entry, make_subdocument, analyst, generate, events
):
    from sgp.documents.layouts import DEFAULT_LOGO
    from sgp.files.storage import media_root

    draft = layouts.create_draft("subdocument", by=quality)
    logo = SimpleUploadedFile("logo.png", DEFAULT_LOGO.read_bytes(), content_type="image/png")
    draft = layouts.update_draft(draft, by=quality, definition=draft.definition, logo_upload=logo)
    layouts.publish(draft, by=quality)
    sub = make_subdocument(project, "formulacao")
    assert layouts.layout_for("subdocument", sub.pk, 1).logo_id == draft.logo_id
    (media_root() / draft.logo.storage_name).write_bytes(b"corrompido")
    pending = generate("subdocument", sub, "pdf", analyst)
    assert pending.status == "failed" and "integridade" in pending.error
    assert events("files.integrity_failed") and events("documents.generation_failed")
