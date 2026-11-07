"""Lotes do projeto (US1: FR-009, FR-010 da feature 003)."""

from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from sgp.accounts.profiles import Profile
from sgp.catalog.models import Lot

pytestmark = [pytest.mark.django_db]


def lot_post(project, responsible, **overrides):
    data = {
        "project": project.pk,
        "code": "LP-001",
        "lot_type": "pilot",
        "manufacture_date": "2026-09-01",
        "expiry_date": "2027-09-01",
        "manufacturing_site": "Planta piloto",
        "production_responsible": responsible.pk,
    }
    data.update(overrides)
    return data


@pytest.fixture
def project(open_project):
    return open_project()


@pytest.fixture
def member(client, project, make_user, member_of):
    user = member_of(project, make_user(None, Profile.ANALYST))
    client.force_login(user)
    return user


@pytest.mark.req("003:FR-009")
def test_analista_da_equipe_cadastra_lote(client, project, member, events):
    response = client.post(reverse("catalog:new", args=["lotes"]), lot_post(project, member))
    lot = Lot.objects.get()
    assert response.status_code == 302
    assert response["Location"] == reverse("catalog:detail", args=["lotes", lot.pk])
    assert (lot.project, lot.code, lot.version, lot.created_by) == (project, "LP-001", 1, member)
    event = events("catalog.created")[-1]
    assert event.project_id == project.pk
    assert event.object_id == str(lot.lineage)


@pytest.mark.req("003:FR-010")
def test_exibicao_padronizada_do_lote(make_user, project, make_lot):
    lot = make_lot(
        project,
        make_user(None, Profile.QUALITY),
        code="LV-07",
        manufacture_date=date(2026, 3, 15),
        expiry_date=date(2028, 2, 1),
    )
    assert lot.display == "Lote LV-07 – Fabricação: 03/2026 – Validade: 02/2028"
    assert str(lot) == lot.display


@pytest.mark.req("003:FR-009")
def test_validade_anterior_a_fabricacao_e_recusada(client, project, member):
    response = client.post(
        reverse("catalog:new", args=["lotes"]),
        lot_post(project, member, expiry_date="2026-08-01"),
    )
    assert response.status_code == 200
    assert "A validade precisa ser posterior à data de fabricação." in response.content.decode()
    assert not Lot.objects.exists()


@pytest.mark.req("003:FR-009")
def test_codigo_repetido_no_projeto_e_recusado(
    client, project, member, make_lot, open_project, make_user
):
    make_lot(project, member)
    response = client.post(reverse("catalog:new", args=["lotes"]), lot_post(project, member))
    assert "Já existe lote vigente com código LP-001 neste projeto." in response.content.decode()
    other = open_project()
    quality = make_user(None, Profile.QUALITY)
    assert make_lot(other, quality).code == "LP-001"


@pytest.mark.req("003:FR-009")
def test_padrao_de_codigo_configuravel(client, project, member, settings):
    response = client.post(
        reverse("catalog:new", args=["lotes"]), lot_post(project, member, code="LP 001")
    )
    assert "Código de lote fora do padrão" in response.content.decode()
    settings.LOT_CODE_PATTERN = r"^LP-\d{3}$"
    response = client.post(
        reverse("catalog:new", args=["lotes"]), lot_post(project, member, code="X-1")
    )
    assert "Código de lote fora do padrão" in response.content.decode()
    client.post(reverse("catalog:new", args=["lotes"]), lot_post(project, member, code="LP-123"))
    assert Lot.objects.filter(code="LP-123").exists()


@pytest.mark.req("003:FR-009")
def test_sem_acesso_ao_projeto_e_negado_e_registrado(
    client, project, make_lot, make_user, login_as, events
):
    lot = make_lot(project, make_user(None, Profile.QUALITY))
    outsider = login_as(Profile.ANALYST)
    response = client.get(reverse("catalog:detail", args=["lotes", lot.pk]))
    assert response.status_code == 403
    assert (
        events("auth.permission_denied")[-1].new_value["motivo"] == "sem acesso ao projeto do lote"
    )
    response = client.post(reverse("catalog:new", args=["lotes"]), lot_post(project, outsider))
    assert response.status_code == 200
    assert not Lot.objects.filter(created_by=outsider).exists()
    listing = client.get(reverse("catalog:list", args=["lotes"])).content.decode()
    assert "LP-001" not in listing


@pytest.mark.req("003:FR-009")
def test_servico_recusa_lote_em_projeto_sem_acesso_ou_fechado(
    project, make_project, make_user, lot_data
):
    from sgp.catalog import versioning
    from sgp.catalog.kinds import LOTS

    outsider = make_user(None, Profile.ANALYST)
    with pytest.raises(ValidationError, match="não tem acesso ao projeto"):
        versioning.create_record(LOTS, by=outsider, data=lot_data(project, outsider))
    quality = make_user(None, Profile.QUALITY)
    with pytest.raises(ValidationError, match="projetos abertos"):
        versioning.create_record(LOTS, by=quality, data=lot_data(make_project(), quality))


@pytest.mark.req("003:FR-009")
def test_lista_mostra_so_lotes_de_projetos_acessiveis(
    client, project, member, make_lot, open_project, make_user
):
    make_lot(project, member, code="LP-AAA")
    make_lot(open_project(), make_user(None, Profile.QUALITY), code="LP-BBB")
    listing = client.get(reverse("catalog:list", args=["lotes"])).content.decode()
    assert "LP-AAA" in listing and "LP-BBB" not in listing
    fragment = client.get(reverse("catalog:search", args=["lotes"]), {"q": "LP-"}).content.decode()
    assert "LP-AAA" in fragment and "LP-BBB" not in fragment


@pytest.mark.req("003:FR-009")
def test_lote_nao_muda_de_projeto(project, make_lot, make_user, open_project):
    from sgp.catalog import versioning

    quality = make_user(None, Profile.QUALITY)
    lot = make_lot(project, quality)
    with pytest.raises(ValidationError, match="não muda de projeto"):
        versioning.update_record(lot, by=quality, data={"project": open_project()})
