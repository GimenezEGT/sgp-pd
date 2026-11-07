"""Quem consulta e quem edita cadastros; lotes pela regra de acesso ao projeto (FR-008, FR-009)."""

import pytest

from sgp.accounts.profiles import Profile
from sgp.catalog.permissions import (
    can_edit_catalog,
    can_edit_record,
    can_view_record,
    lot_projects,
)

pytestmark = [pytest.mark.django_db]


@pytest.mark.req("003:FR-008")
@pytest.mark.parametrize(
    "profile,expected",
    [
        (Profile.ANALYST, True),
        (Profile.PROJECT_LEADER, True),
        (Profile.RD_MANAGER, True),
        (Profile.QUALITY, True),
        (Profile.READER, False),
        (Profile.ADMIN, False),
    ],
)
def test_editores_dos_cadastros(make_user, profile, expected):
    assert can_edit_catalog(make_user(None, profile)) is expected


@pytest.mark.req("003:FR-008")
def test_sem_perfil_nao_consulta(make_user, make_material):
    owner = make_user(None, Profile.ANALYST)
    material = make_material(owner)
    assert can_view_record(make_user(None, Profile.READER), material)
    assert not can_view_record(make_user(), material)


@pytest.mark.req("003:FR-009")
def test_lote_segue_o_acesso_ao_projeto(make_user, open_project, make_lot, member_of):
    project = open_project()
    quality = make_user(None, Profile.QUALITY)
    lot = make_lot(project, quality)
    outsider = make_user(None, Profile.ANALYST)
    assert not can_view_record(outsider, lot)
    assert not can_edit_record(outsider, lot)
    member = member_of(project, make_user(None, Profile.ANALYST))
    assert can_view_record(member, lot) and can_edit_record(member, lot)
    reader = make_user(None, Profile.READER)
    assert not can_view_record(reader, lot)
    manager = make_user(None, Profile.RD_MANAGER)
    assert can_view_record(manager, lot)


@pytest.mark.req("003:FR-009")
def test_lotes_so_em_projetos_abertos_e_acessiveis(
    make_user, open_project, make_project, member_of
):
    project = open_project()
    draft = make_project()
    member = member_of(project, make_user(None, Profile.ANALYST))
    assert list(lot_projects(member)) == [project]
    quality = make_user(None, Profile.QUALITY)
    assert draft not in lot_projects(quality) and project in lot_projects(quality)
