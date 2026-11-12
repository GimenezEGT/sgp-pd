"""Publicação, vigência, documentos iniciados e integridade (FR-010, FR-012 a FR-014, SC-002,
SC-003)."""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import connection
from django.utils import timezone

from sgp.formtemplates import services as forms
from sgp.revisions import services
from sgp.revisions.models import Step, TemplateStep

pytestmark = [pytest.mark.django_db]


@pytest.mark.req("013:FR-010")
@pytest.mark.req("013:FR-013")
def test_vigencia_imediata_e_documento_iniciado_fica_na_versao_dele(
    submitted,
    approver,
    signing,
    rapd_type,
    project,
    approved_entry,
    make_subdocument,
    approve_quick,
):
    for code in ("formulacao", "lote-piloto"):
        approve_quick(make_subdocument(project, code))
    started = make_subdocument(project, "rapd")
    services.approve("form", submitted, by=approver, password=signing.password)
    started.refresh_from_db()
    assert started.template.form_version == 5
    old = forms.FormTemplate.objects.get(subdocument_type=rapd_type, form_version=5)
    assert services.situation(services.get_adapter("form"), old) == "superseded"


@pytest.mark.req("013:FR-010")
@pytest.mark.req("013:SC-002")
def test_vigencia_futura_aguarda_a_data_e_e_registrada_uma_vez(
    submitted, approver, signing, rapd_type, events, quality
):
    future = timezone.localdate() + datetime.timedelta(days=10)
    approved = services.approve(
        "form", submitted, by=approver, password=signing.password, valid_from=future
    )
    adapter = services.get_adapter("form")
    assert services.situation(adapter, approved) == "pending"
    assert forms.current_template(rapd_type).form_version == 5
    with pytest.raises(ValidationError, match="aguardando vigência"):
        forms.create_draft(rapd_type, by=quality)
    assert services.record_due() == 0
    assert services.record_due(today=future) == 1
    assert services.record_due(today=future) == 0
    steps = TemplateStep.objects.filter(template_id=approved.pk, step=Step.BECAME_CURRENT)
    assert steps.count() == 1 and events("templates.became_current")


@pytest.mark.req("013:FR-010")
def test_vigencia_no_passado_e_recusada(submitted, approver, signing):
    with pytest.raises(ValidationError, match="anterior a hoje"):
        services.approve(
            "form",
            submitted,
            by=approver,
            password=signing.password,
            valid_from=datetime.date(2020, 1, 1),
        )


@pytest.mark.req("013:FR-012")
@pytest.mark.req("013:FR-014")
@pytest.mark.req("013:SC-003")
def test_publicada_nao_muda_e_adulteracao_no_banco_e_apontada(
    submitted, approver, signing, quality, events
):
    approved = services.approve("form", submitted, by=approver, password=signing.password)
    with pytest.raises(ValidationError, match="publicado não muda"):
        forms.update_draft(approved, by=quality, data={}, definition=approved.definition)
    assert services.verify("form", approved, by=quality)["integro"] is True
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute(
            "ALTER TABLE formtemplates_formtemplate DISABLE TRIGGER formtemplates_published_immutable"
        )
        cursor.execute(
            "UPDATE formtemplates_formtemplate SET reference = 'adulterada' WHERE id = %s",
            [approved.pk],
        )
        cursor.execute(
            "ALTER TABLE formtemplates_formtemplate ENABLE TRIGGER formtemplates_published_immutable"
        )
    result = services.verify("form", approved, by=approver)
    assert result["integro"] is False and any("divergente" in p for p in result["problemas"])
    assert [e.new_value["integro"] for e in events("templates.verified")] == [True, False]


@pytest.mark.req("013:FR-014")
def test_versao_anterior_a_013_tem_resumo_de_base_ou_e_informada(quality, rapd_type):
    seeded = forms.current_template(rapd_type)
    assert seeded.approved_hash  # resumo de base gravado na implantação da 013
    assert services.verify("form", seeded, by=quality)["integro"] is True
    forms.FormTemplate.objects.filter(pk=seeded.pk).update(approved_hash="")
    result = services.verify("form", seeded, by=quality)
    assert result["integro"] is False and "antes da revisão controlada" in result["problemas"][0]


@pytest.mark.req("013:FR-005")
@pytest.mark.req("013:FR-012")
def test_reverter_e_nova_revisao_com_o_conteudo_da_versao_antiga(
    submitted, approver, signing, quality, rapd_type
):
    services.approve("form", submitted, by=approver, password=signing.password)
    old = forms.FormTemplate.objects.get(subdocument_type=rapd_type, form_version=5)
    revert = forms.create_draft(rapd_type, by=quality, source=old)
    assert revert.form_version == 7 and revert.definition == old.definition
    services.submit("form", revert, by=quality, reason="Reverter o rótulo", impact="Novos RAPD")
    services.approve("form", revert, by=approver, password=signing.password)
    assert forms.current_template(rapd_type).form_version == 7
    old.refresh_from_db()
    assert old.status == "published"  # a versão antiga não é reativada nem alterada
