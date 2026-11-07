"""Versões, bloqueio e desativação dos cadastros (FR-002 a FR-006, SC-001 da feature 003)."""

import pytest
from django.core.exceptions import ValidationError
from django.db import ProgrammingError

from sgp.accounts.profiles import Profile
from sgp.catalog import versioning
from sgp.catalog.kinds import MATERIALS
from sgp.catalog.models import Material
from tests.db_helpers import app_role_exists, run_as_app_role

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def editor(make_user):
    return make_user(None, Profile.ANALYST)


@pytest.mark.req("003:FR-001")
def test_cria_a_versao_1_com_evento(editor, make_material, events):
    material = make_material(editor, code="MP-100", description="Cloreto de sódio")
    assert (material.version, material.is_current, material.is_active) == (1, True, True)
    event = events("catalog.created")[-1]
    assert event.object_type == "catalog.material"
    assert event.object_id == str(material.lineage)
    assert event.new_value["code"] == "MP-100"
    assert event.new_value["versao"] == 1 and event.new_value["registro"] == material.pk
    assert event.new_value["material_type"] == "Matéria-prima"


@pytest.mark.req("003:FR-002")
def test_correcao_no_proprio_registro_quando_nao_bloqueado(editor, make_material, events):
    material = make_material(editor, description="Cloreto de sodio")
    result, outcome = versioning.update_record(
        material, by=editor, data={"description": "Cloreto de sódio P.A."}
    )
    assert outcome == versioning.UPDATED
    assert result.pk == material.pk and result.version == 1
    assert Material.objects.filter(lineage=material.lineage).count() == 1
    event = events("catalog.updated")[-1]
    assert event.old_value == {"description": "Cloreto de sodio"}
    assert event.new_value["description"] == "Cloreto de sódio P.A."
    assert event.new_value["versao"] == 1


@pytest.mark.req("003:FR-003")
@pytest.mark.req("003:SC-001")
def test_bloqueado_exige_motivo_e_cria_nova_versao(editor, make_material, events):
    material = make_material(editor, manufacturer="Fornecedor A")
    versioning.lock_version(material, by=editor, reason="Usado na Formulação v01 assinada")
    with pytest.raises(ValidationError, match="exige o motivo"):
        versioning.update_record(material, by=editor, data={"manufacturer": "Fornecedor B"})
    successor, outcome = versioning.update_record(
        material, by=editor, data={"manufacturer": "Fornecedor B"}, reason="Troca de fornecedor"
    )
    assert outcome == versioning.VERSIONED
    assert (successor.version, successor.is_current, successor.is_locked) == (2, True, False)
    assert successor.version_reason == "Troca de fornecedor"
    original = Material.objects.get(pk=material.pk)
    assert original.manufacturer == "Fornecedor A"
    assert not original.is_current and original.is_locked
    event = events("catalog.versioned")[-1]
    assert event.reason == "Troca de fornecedor"
    assert event.old_value == {"manufacturer": "Fornecedor A"}
    assert event.new_value["versao"] == 2 and event.new_value["registro"] == successor.pk


@pytest.mark.req("003:FR-004")
def test_codigo_nao_muda_depois_de_qualquer_bloqueio(editor, make_material):
    material = make_material(editor, code="MP-200")
    versioning.lock_version(material, by=editor, reason="Documento assinado")
    with pytest.raises(ValidationError, match="código não pode mudar"):
        versioning.update_record(material, by=editor, data={"code": "MP-201"}, reason="Erro")
    successor, _ = versioning.update_record(
        material, by=editor, data={"description": "Nova descrição"}, reason="Correção"
    )
    with pytest.raises(ValidationError, match="código não pode mudar"):
        versioning.update_record(successor, by=editor, data={"code": "MP-201"})


@pytest.mark.req("003:FR-002")
def test_codigo_muda_enquanto_nunca_foi_bloqueado(editor, make_material):
    material = make_material(editor, code="MP-300")
    result, outcome = versioning.update_record(material, by=editor, data={"code": "MP-301"})
    assert outcome == versioning.UPDATED and result.code == "MP-301"


@pytest.mark.req("003:FR-002")
def test_correcao_sem_mudanca_nao_gera_versao_nem_evento(editor, make_material, events):
    material = make_material(editor)
    versioning.lock_version(material, by=editor, reason="Assinado")
    before = len(events())
    result, outcome = versioning.update_record(
        material, by=editor, data={"description": material.description}, reason="Nada mudou"
    )
    assert outcome == versioning.UNCHANGED and result.pk == material.pk
    assert len(events()) == before
    assert Material.objects.filter(lineage=material.lineage).count() == 1


@pytest.mark.req("003:FR-005")
def test_historico_tem_todas_as_versoes(editor, make_material):
    material = make_material(editor)
    versioning.lock_version(material, by=editor, reason="Assinado")
    second, _ = versioning.update_record(
        material, by=editor, data={"manufacturer_lot": "F-200"}, reason="Lote novo"
    )
    versioning.lock_version(second, by=editor, reason="Assinado de novo")
    third, _ = versioning.update_record(
        second, by=editor, data={"manufacturer_lot": "F-300"}, reason="Outro lote"
    )
    versions = list(versioning.history(third))
    assert [version.version for version in versions] == [3, 2, 1]
    assert [version.version_reason for version in versions] == ["Outro lote", "Lote novo", ""]
    assert all(version.created_by == editor for version in versions)


@pytest.mark.req("003:FR-003")
def test_versao_substituida_nao_e_corrigida(editor, make_material):
    material = make_material(editor)
    versioning.lock_version(material, by=editor, reason="Assinado")
    versioning.update_record(material, by=editor, data={"manufacturer": "Outro"}, reason="Troca")
    with pytest.raises(ValidationError, match="substituída"):
        versioning.update_record(material, by=editor, data={"manufacturer": "Mais um"})


@pytest.mark.req("003:FR-002")
def test_edicao_simultanea_e_recusada(editor, make_material):
    material = make_material(editor)
    versioning.update_record(material, by=editor, data={"manufacturer": "A"}, row_version=1)
    with pytest.raises(ValidationError, match="Outra pessoa gravou"):
        versioning.update_record(material, by=editor, data={"manufacturer": "B"}, row_version=1)


@pytest.mark.req("003:FR-003")
def test_bloquear_de_novo_nao_gera_evento(editor, make_material, events):
    material = make_material(editor)
    versioning.lock_version(material, by=editor, reason="Assinado")
    versioning.lock_version(material, by=editor, reason="Assinado de novo")
    assert len(events("catalog.locked")) == 1
    assert events("catalog.locked")[0].new_value == {"versao": 1, "registro": material.pk}


@pytest.mark.req("003:FR-006")
def test_desativacao_e_reativacao_com_motivo(editor, make_material, events):
    material = make_material(editor)
    with pytest.raises(ValidationError, match="motivo"):
        versioning.set_active(material, by=editor, active=False, reason="")
    versioning.set_active(material, by=editor, active=False, reason="Fora de linha")
    assert not Material.objects.available().filter(pk=material.pk).exists()
    assert Material.objects.current().filter(pk=material.pk).exists()
    with pytest.raises(ValidationError, match="já está desativado"):
        versioning.set_active(material, by=editor, active=False, reason="De novo")
    versioning.set_active(material, by=editor, active=True, reason="Voltou a ser usado")
    deactivated, reactivated = events("catalog.deactivated")[-1], events("catalog.reactivated")[-1]
    assert deactivated.old_value == {"ativo": True} and deactivated.reason == "Fora de linha"
    assert reactivated.new_value["ativo"] is True


@pytest.mark.req("003:FR-008")
def test_perfil_de_consulta_nao_cadastra(make_user):
    reader = make_user(None, Profile.READER)
    with pytest.raises(ValidationError, match="só consulta"):
        versioning.create_record(
            MATERIALS,
            by=reader,
            data={"code": "X-1", "description": "Teste", "material_type": "raw"},
        )


@pytest.mark.req("003:FR-011")
def test_codigo_unico_entre_os_vigentes(editor, make_material):
    make_material(editor, code="MP-900")
    with pytest.raises(ValidationError, match="Já existe insumo vigente"):
        make_material(editor, code="MP-900")


@pytest.mark.req("003:FR-006")
def test_papel_da_aplicacao_nao_apaga_cadastros(editor, make_material):
    material = make_material(editor)
    with pytest.raises(Exception, match="não são apagados"):
        material.delete()
    if not app_role_exists():
        pytest.skip("Papel da aplicação inexistente neste banco.")
    with pytest.raises(ProgrammingError, match="permission denied"):
        run_as_app_role("DELETE FROM catalog_material WHERE id = %s", [material.pk])
