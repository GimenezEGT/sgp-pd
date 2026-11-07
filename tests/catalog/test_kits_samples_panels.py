"""Kits de referência, amostras e painéis (US4: FR-014, FR-017 da feature 003)."""

from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from sgp.accounts.profiles import Profile
from sgp.catalog import versioning
from sgp.catalog.forms import SampleForm
from sgp.catalog.kinds import PANELS, REFERENCE_KITS
from sgp.catalog.models import PanelSample, Sample
from sgp.vocab import services as vocab_services
from sgp.vocab.models import Term, get_term

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def editor(make_user):
    return make_user(None, Profile.ANALYST)


def make_panel(by, samples, code="PN-01"):
    return versioning.create_record(
        PANELS, by=by, data={"code": code, "description": "Painel de teste"}, samples=samples
    )


@pytest.mark.req("003:FR-014")
def test_kit_de_referencia_com_registro(editor):
    kit = versioning.create_record(
        REFERENCE_KITS,
        by=editor,
        data={
            "name": "Kit comparativo X",
            "manufacturer": "Fabricante Y",
            "lot": "K-55",
            "expiry_date": date(2027, 6, 30),
            "registration_number": "80000000001",
        },
    )
    assert kit.display == (
        "Kit comparativo X – Fabricante Y – Lote K-55 – Validade: 06/2027 – Registro 80000000001"
    )
    without = versioning.create_record(
        REFERENCE_KITS,
        by=editor,
        data={"name": "Kit Z", "manufacturer": "F", "lot": "1", "expiry_date": date(2027, 1, 1)},
    )
    assert "Registro" not in without.display


@pytest.mark.req("003:FR-017")
def test_painel_referencia_versoes_e_amostra_em_varios_paineis(editor, make_sample, events):
    first, second = make_sample(editor), make_sample(editor)
    panel_a = make_panel(editor, [first, second], code="PN-A")
    panel_b = make_panel(editor, [first], code="PN-B")
    assert panel_a.samples() == [first, second]
    assert panel_b.samples() == [first]
    assert events("catalog.created")[-1].new_value["amostras"] == [f"{first.identifier} v01"]


@pytest.mark.req("003:FR-017")
def test_painel_nao_aceita_duas_versoes_da_mesma_amostra(editor, make_sample):
    sample = make_sample(editor)
    versioning.lock_version(sample, by=editor, reason="Assinada")
    successor, _ = versioning.update_record(
        sample, by=editor, data={"origin": "Outro banco"}, reason="Correção"
    )
    with pytest.raises(ValidationError, match="duas versões da mesma amostra"):
        make_panel(editor, [sample, successor])


@pytest.mark.req("003:FR-017")
def test_nova_versao_da_amostra_mantem_o_painel_na_versao_antiga(editor, make_sample):
    sample = make_sample(editor)
    panel = make_panel(editor, [sample])
    versioning.lock_version(sample, by=editor, reason="Estudo assinado")
    successor, _ = versioning.update_record(
        sample, by=editor, data={"characterization": "Reagente; 15 U/mL"}, reason="Reanálise"
    )
    assert panel.samples() == [Sample.objects.get(pk=sample.pk)]
    assert successor.pk != sample.pk
    updated, outcome = versioning.update_record(panel, by=editor, data={}, samples=[successor])
    assert outcome == versioning.UPDATED
    assert updated.samples() == [successor]
    removed = PanelSample.objects.get(panel=panel, sample=sample)
    assert removed.removed_at is not None and removed.removed_by == editor


@pytest.mark.req("003:FR-017")
def test_bloquear_painel_bloqueia_as_amostras(editor, make_sample, events):
    first, second = make_sample(editor), make_sample(editor)
    panel = make_panel(editor, [first, second])
    versioning.lock_version(panel, by=editor, reason="Validação v01 assinada")
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.is_locked and second.is_locked
    assert len(events("catalog.locked")) == 3


@pytest.mark.req("003:FR-017")
def test_painel_bloqueado_ganha_nova_versao_com_as_amostras(editor, make_sample):
    first, second = make_sample(editor), make_sample(editor)
    panel = make_panel(editor, [first])
    versioning.lock_version(panel, by=editor, reason="Assinado")
    successor, outcome = versioning.update_record(
        panel, by=editor, data={}, samples=[first, second], reason="Inclusão de amostra"
    )
    assert outcome == versioning.VERSIONED
    assert successor.samples() == [first, second]
    assert panel.samples() == [first]


@pytest.mark.req("003:FR-017")
def test_amostra_desativada_aparece_no_painel_com_indicacao(client, editor, make_sample):
    sample = make_sample(editor)
    panel = make_panel(editor, [sample])
    versioning.set_active(sample, by=editor, active=False, reason="Amostra esgotada")
    client.force_login(editor)
    page = client.get(reverse("catalog:detail", args=["paineis", panel.pk])).content.decode()
    assert sample.identifier in page and "Desativada" in page


@pytest.mark.req("003:FR-019")
def test_termo_desativado_fora_dos_novos_e_mantido_nos_antigos(editor, make_sample, make_user):
    liquor = get_term("tipo-amostra", "liquor")
    sample = make_sample(editor, sample_type=liquor)
    quality = make_user(None, Profile.QUALITY)
    vocab_services.set_term_active(liquor, by=quality, active=False, reason="Não usado")
    new_form = SampleForm(user=editor)
    assert liquor not in new_form.fields["sample_type"].queryset
    edit_form = SampleForm(user=editor, instance=Sample.objects.get(pk=sample.pk))
    assert liquor in edit_form.fields["sample_type"].queryset
    assert Term.objects.get(pk=liquor.pk).label == "Líquor"


@pytest.mark.req("003:FR-017")
def test_painel_pela_tela(client, editor, make_sample):
    first, second = make_sample(editor), make_sample(editor)
    client.force_login(editor)
    response = client.post(
        reverse("catalog:new", args=["paineis"]),
        {"code": "PN-T", "description": "Painel da tela", "samples": [first.pk, second.pk]},
    )
    assert response.status_code == 302
    from sgp.catalog.models import Panel

    panel = Panel.objects.get(code="PN-T")
    assert panel.samples() == [first, second]
    edit = client.get(reverse("catalog:edit", args=["paineis", panel.pk])).content.decode()
    assert first.identifier in edit
