"""Pendências antes de gerar (FR-012, SC-002)."""

import pytest

from sgp.fulldoc.pending import pending_items
from sgp.signatures.canonical import content_hash
from sgp.signatures.models import ApprovedVersion

pytestmark = [pytest.mark.req("009:FR-012"), pytest.mark.req("009:SC-002")]


def test_projeto_completo_nao_tem_pendencias(complete_project):
    assert pending_items(complete_project()) == []


def test_tipos_do_fluxo_sem_versao_aprovada(signed_project, create_sub, force_approve):
    force_approve(create_sub(signed_project, "entrada"))
    create_sub(signed_project, "formulacao")
    items = pending_items(signed_project)
    assert items[0].startswith("Elaboração de Formulação") or "Formulação" in items[0]
    assert any("sem versão aprovada" in item for item in items)
    assert any(item.startswith("Saída de Projeto") or "Saída" in item for item in items)
    assert not any("Termo de Abertura" in item for item in items)


def test_versao_aprovada_sem_conteudo_congelado(signed_project, create_sub, manager):
    sub = create_sub(signed_project, "entrada")
    ApprovedVersion.objects.create(
        kind="subdocument",
        object_id=sub.pk,
        project=signed_project,
        version=1,
        content={"topicos": {}},
        content_hash=content_hash({"topicos": {}}),
        approved_by=manager,
    )
    assert any("sem conteúdo congelado" in item for item in pending_items(signed_project))


def test_itens_da_verificacao_final_diferentes_de_aprovado(complete_project):
    items = pending_items(complete_project(rejected=True))
    assert len(items) == 1
    assert "Verificação Final, item 2 – Funcionalidade" in items[0]
    assert "Reprovado" in items[0] and "Fora do critério combinado" in items[0]


def test_projeto_aprovado_sem_assinatura_aponta_tap_e_plano(open_project):
    items = pending_items(open_project())
    assert items[0].startswith("Termo de Abertura do Projeto: sem versão aprovada")
    assert items[1].startswith("Plano de Negócios: sem versão aprovada")
