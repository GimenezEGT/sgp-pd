"""Versões e bloqueio pelas telas (US2: FR-002 a FR-005, SC-001 da feature 003)."""

import pytest
from django.urls import reverse

from sgp.accounts.profiles import Profile
from sgp.catalog import versioning
from sgp.catalog.models import Lot

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def quality(client, make_user):
    user = make_user(None, Profile.QUALITY)
    client.force_login(user)
    return user


@pytest.fixture
def locked_lot(open_project, make_lot, quality):
    lot = make_lot(open_project(), quality)
    return versioning.lock_version(lot, by=quality, reason="Elaboração de Lote Piloto v01 assinada")


def edit_post(lot, **overrides):
    data = {
        "project": lot.project_id,
        "code": lot.code,
        "lot_type": lot.lot_type,
        "manufacture_date": lot.manufacture_date.isoformat(),
        "expiry_date": lot.expiry_date.isoformat(),
        "manufacturing_site": lot.manufacturing_site,
        "production_responsible": lot.production_responsible_id,
        "row_version": lot.row_version,
        "reason": "",
    }
    data.update(overrides)
    return data


@pytest.mark.req("003:FR-003")
def test_tela_avisa_e_exige_motivo_quando_bloqueado(client, locked_lot):
    page = client.get(reverse("catalog:edit", args=["lotes", locked_lot.pk])).content.decode()
    assert "cria a versão 02" in page
    response = client.post(
        reverse("catalog:edit", args=["lotes", locked_lot.pk]),
        edit_post(locked_lot, expiry_date="2027-12-01"),
    )
    assert response.status_code == 200
    assert "Este campo é obrigatório" in response.content.decode()
    assert Lot.objects.filter(lineage=locked_lot.lineage).count() == 1


@pytest.mark.req("003:FR-003")
@pytest.mark.req("003:SC-001")
def test_correcao_com_motivo_cria_versao_2_e_a_1_fica_igual(client, locked_lot):
    response = client.post(
        reverse("catalog:edit", args=["lotes", locked_lot.pk]),
        edit_post(locked_lot, expiry_date="2027-12-01", reason="Validade corrigida pelo laudo"),
        follow=True,
    )
    successor = Lot.objects.get(lineage=locked_lot.lineage, is_current=True)
    assert successor.version == 2
    assert "Nova versão 02 criada" in response.content.decode()
    original = Lot.objects.get(pk=locked_lot.pk)
    assert original.expiry_date.isoformat() == "2027-09-01"
    assert original.display.endswith("Validade: 09/2027")
    assert successor.display.endswith("Validade: 12/2027")
    old_page = client.get(reverse("catalog:detail", args=["lotes", original.pk])).content.decode()
    assert "Validade: 09/2027" in old_page
    assert "Ver a versão vigente (02)" in old_page


@pytest.mark.req("003:FR-004")
def test_codigo_de_lote_bloqueado_nao_muda(client, locked_lot):
    response = client.post(
        reverse("catalog:edit", args=["lotes", locked_lot.pk]),
        edit_post(locked_lot, code="LP-999", reason="Tentativa"),
    )
    assert "O código não pode mudar" in response.content.decode()
    assert not Lot.objects.filter(code="LP-999").exists()


@pytest.mark.req("003:FR-002")
def test_lote_nao_bloqueado_e_corrigido_no_lugar(client, open_project, make_lot, quality, events):
    lot = make_lot(open_project(), quality)
    client.post(
        reverse("catalog:edit", args=["lotes", lot.pk]),
        edit_post(lot, manufacturing_site="Planta 2"),
    )
    lot.refresh_from_db()
    assert lot.manufacturing_site == "Planta 2" and lot.version == 1
    event = events("catalog.updated")[-1]
    assert event.old_value == {"manufacturing_site": "Planta piloto"}


@pytest.mark.req("003:FR-005")
def test_historico_mostra_versoes_autor_e_motivo(client, locked_lot, quality):
    client.post(
        reverse("catalog:edit", args=["lotes", locked_lot.pk]),
        edit_post(locked_lot, expiry_date="2027-12-01", reason="Validade corrigida pelo laudo"),
    )
    successor = Lot.objects.get(lineage=locked_lot.lineage, is_current=True)
    page = client.get(reverse("catalog:detail", args=["lotes", successor.pk])).content.decode()
    assert "Validade corrigida pelo laudo" in page
    assert "Elaboração de Lote Piloto v01 assinada" in page
    assert quality.get_full_name() in page
    assert "Nova versão de cadastro" in page and "Cadastro bloqueado por documento assinado" in page


@pytest.mark.req("003:FR-003")
def test_editar_versao_substituida_leva_a_vigente(client, locked_lot):
    client.post(
        reverse("catalog:edit", args=["lotes", locked_lot.pk]),
        edit_post(locked_lot, expiry_date="2027-12-01", reason="Correção"),
    )
    successor = Lot.objects.get(lineage=locked_lot.lineage, is_current=True)
    response = client.get(reverse("catalog:edit", args=["lotes", locked_lot.pk]))
    assert response["Location"] == reverse("catalog:edit", args=["lotes", successor.pk])


@pytest.mark.req("003:FR-002")
def test_conflito_de_edicao_simultanea(client, open_project, make_lot, quality):
    lot = make_lot(open_project(), quality)
    stale = edit_post(lot, manufacturing_site="Planta 3")
    client.post(
        reverse("catalog:edit", args=["lotes", lot.pk]),
        edit_post(lot, manufacturing_site="Planta 2"),
    )
    response = client.post(reverse("catalog:edit", args=["lotes", lot.pk]), stale)
    assert "Outra pessoa gravou este cadastro" in response.content.decode()
    lot.refresh_from_db()
    assert lot.manufacturing_site == "Planta 2"


@pytest.mark.req("003:FR-006")
def test_desativar_pela_tela_exige_motivo(client, open_project, make_lot, quality):
    lot = make_lot(open_project(), quality)
    url = reverse("catalog:status", args=["lotes", lot.pk])
    client.post(url, {"action": "desativar", "reason": ""})
    lot.refresh_from_db()
    assert lot.is_active
    client.post(url, {"action": "desativar", "reason": "Lote descartado"})
    lot.refresh_from_db()
    assert not lot.is_active
    fragment = client.get(reverse("catalog:search", args=["lotes"]), {"q": "LP"}).content.decode()
    assert "LP-001" not in fragment
