"""Elaborar, enviar, devolver e aprovar revisões de modelo (FR-001 a FR-009, FR-016, FR-017)."""

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from sgp.accounts.profiles import Profile
from sgp.formtemplates import services as forms
from sgp.revisions import services
from sgp.revisions.models import Step, TemplateSignature, TemplateStep

pytestmark = [pytest.mark.django_db]


@pytest.mark.req("013:FR-005")
@pytest.mark.req("013:FR-006")
def test_revisao_nasce_da_vigente_sem_muda_la(form_draft, quality, rapd_type):
    current = forms.current_template(rapd_type)
    assert (current.form_version, form_draft.form_version) == (5, 6)
    assert form_draft.status == "draft" and form_draft.review_status == "editing"
    assert current.definition["topics"][0]["label"] == "Formulações propostas"
    steps = TemplateStep.objects.filter(kind="form", template_id=form_draft.pk)
    assert [s.step for s in steps] == [Step.OPENED]
    with pytest.raises(ValidationError, match="Já existe um rascunho"):
        forms.create_draft(rapd_type, by=quality)


@pytest.mark.req("013:FR-007")
def test_envio_exige_motivo_impacto_e_mudanca(form_draft, quality, rapd_type):
    with pytest.raises(ValidationError) as error:
        services.submit("form", form_draft, by=quality, reason=" ", impact="")
    assert "Informe o motivo da revisão." in error.value.messages
    assert "Descreva o impacto esperado." in error.value.messages
    unchanged = forms.update_draft(
        form_draft, by=quality, data={}, definition=forms.current_template(rapd_type).definition
    )
    with pytest.raises(ValidationError, match="não muda nada"):
        services.submit("form", unchanged, by=quality, reason="x", impact="y")


@pytest.mark.req("013:FR-007")
def test_rotulo_repetido_impede_o_envio(form_draft, quality):
    definition = dict(form_draft.definition)
    definition["topics"] = form_draft.topics + [dict(form_draft.topics[0], key="copia")]
    draft = forms.update_draft(form_draft, by=quality, data={}, definition=definition)
    with pytest.raises(ValidationError) as error:
        services.submit("form", draft, by=quality, reason="x", impact="y")
    assert any("rótulo repetido" in m for m in error.value.messages)


@pytest.mark.req("013:FR-008")
@pytest.mark.req("013:FR-016")
def test_enviada_nao_muda_e_devolucao_exige_comentario(submitted, quality, approver, events):
    assert submitted.review_status == "submitted" and submitted.submitted_by == quality
    with pytest.raises(ValidationError, match="não muda"):
        forms.update_draft(submitted, by=quality, data={}, definition=submitted.definition)
    with pytest.raises(ValidationError, match="comentário"):
        services.return_revision("form", submitted, by=approver, comment=" ")
    returned = services.return_revision("form", submitted, by=approver, comment="Rever o rótulo")
    assert returned.review_status == "editing"
    step = TemplateStep.objects.filter(template_id=submitted.pk, step=Step.RETURNED).get()
    assert step.comment == "Rever o rótulo" and step.actor == approver
    assert events("templates.returned")[-1].reason == "Rever o rótulo"
    assert events("templates.submitted")[-1].new_value["mudancas"] == 1


@pytest.mark.req("013:FR-009")
@pytest.mark.req("013:FR-017")
def test_aprovacao_com_assinatura_publica_e_registra(
    submitted, approver, signing, rapd_type, events
):
    approved = services.approve("form", submitted, by=approver, password=signing.password)
    assert approved.status == "published" and approved.approved_hash
    assert forms.current_template(rapd_type) == approved
    signature = TemplateSignature.objects.get(template_id=approved.pk, purpose="approval")
    assert signature.content_hash == approved.approved_hash and signature.signer == approver
    steps = [s.step for s in TemplateStep.objects.filter(template_id=approved.pk)]
    assert steps == [Step.OPENED, Step.SUBMITTED, Step.APPROVED, Step.BECAME_CURRENT]
    for event_type in ("templates.approved", "formtemplates.published", "templates.became_current"):
        assert events(event_type)


@pytest.mark.req("013:FR-003")
@pytest.mark.req("013:FR-002")
def test_quem_elaborou_nao_aprova_e_perfis_sao_exigidos(
    submitted, quality, make_user, signing, approver
):
    double = make_user(None, Profile.QUALITY, Profile.RD_MANAGER)
    signing.enable(double)
    draft_by_double = submitted
    with pytest.raises(ValidationError, match="Só o Gestor"):
        services.approve("form", submitted, by=quality, password=signing.password)
    from sgp.revisions.models import ReviewStatus

    type(submitted).objects.filter(pk=submitted.pk).update(created_by=double)
    with pytest.raises(ValidationError, match="Quem elaborou ou enviou"):
        services.approve("form", draft_by_double, by=double, password=signing.password)
    analyst = make_user(None, Profile.ANALYST)
    with pytest.raises(ValidationError, match="Só a Qualidade"):
        services.discard("form", submitted, by=analyst, reason="x")
    assert submitted.review_status == ReviewStatus.SUBMITTED


@pytest.mark.req("013:FR-009")
def test_senha_errada_conta_para_o_bloqueio_da_005(submitted, approver, events):
    for attempt in range(3):
        with pytest.raises(ValidationError):
            services.approve("form", submitted, by=approver, password=f"errada{attempt}")
    assert events("signatures.blocked")
    submitted.refresh_from_db()
    assert submitted.status == "draft"


@pytest.mark.req("013:FR-002")
def test_aprovador_que_perdeu_o_perfil_e_recusado(submitted, approver, signing):
    from sgp.accounts.models import ProfileAssignment

    ProfileAssignment.objects.filter(user=approver).update(revoked_at="2026-01-01T00:00:00Z")
    from sgp.accounts.profiles import clear_profile_cache

    clear_profile_cache(approver)
    with pytest.raises(ValidationError, match="Só o Gestor"):
        services.approve("form", submitted, by=approver, password=signing.password)


@pytest.mark.req("013:FR-004")
@pytest.mark.req("013:FR-001")
@pytest.mark.req("013:SC-001")
def test_telas_negam_sem_perfil_e_ciclo_pela_tela(
    client, login_as, submitted, approver, signing, events
):
    login_as(Profile.ANALYST)
    assert client.post(reverse("revisions:submit", args=["form", submitted.pk])).status_code == 403
    assert client.get(reverse("revisions:approve", args=["form", submitted.pk])).status_code == 403
    assert len(events("auth.permission_denied")) == 2
    assert client.get(reverse("revisions:list")).status_code == 200
    client.force_login(approver)
    page = client.get(reverse("revisions:approve", args=["form", submitted.pk])).content.decode()
    assert "Formulações propostas (revisado)" in page and "Ajuste de rótulo" in page
    client.post(
        reverse("revisions:approve", args=["form", submitted.pk]),
        {"senha": signing.password, "vigencia": "imediata"},
    )
    submitted.refresh_from_db()
    assert submitted.status == "published"


@pytest.mark.req("013:FR-001")
def test_layout_segue_o_mesmo_ciclo(quality, approver, signing, vocab_seed):
    from sgp.documents import layouts

    draft = layouts.create_draft("charter", by=quality)
    definition = draft.definition
    definition["footer"]["text"] = "Formulário do TAP – {projeto}"
    draft = layouts.update_draft(draft, by=quality, definition=definition)
    services.submit("layout", draft, by=quality, reason="Rodapé do TAP", impact="TAP novos")
    approved = services.approve("layout", draft, by=approver, password=signing.password)
    assert layouts.current_layout("charter") == approved and approved.approved_hash
