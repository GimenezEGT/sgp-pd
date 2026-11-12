"""Conteúdo congelado na aprovação e regeneração idêntica (FR-017, SC-005)."""

import pytest

from sgp.documents import content, render_pdf, services
from sgp.documents.models import FrozenRendering
from sgp.projects.models import Project
from sgp.vocab.models import Term

pytestmark = [pytest.mark.django_db]


@pytest.mark.req("006:FR-017")
def test_aprovacao_congela_o_conteudo_com_assinaturas(approved_entry, events):
    rendering = FrozenRendering.objects.get(
        kind="subdocument", object_id=approved_entry.pk, version=1
    )
    meanings = [s["meaning_code"] for s in rendering.content["signatures"]]
    assert meanings == ["elaborated", "approved"]
    assert rendering.content["approved_on"] and rendering.content["approved_hash"]
    frozen_event = events("documents.frozen")[-1]
    assert frozen_event.new_value["resumo"] == rendering.content_hash


@pytest.mark.req("006:FR-017")
@pytest.mark.req("006:SC-005")
def test_regeneracao_identica_mesmo_depois_de_mudar_produto_e_rotulo(
    approved_entry, analyst, quality, generate, seal_cert
):
    from sgp.vocab import services as vocab

    first = generate("subdocument", approved_entry, "pdf", analyst).result
    Project.objects.filter(pk=approved_entry.project_id).update(product_name="PRODUTO RENOMEADO")
    term = Term.objects.of("tipo-amostra").get(code="soro")
    vocab.relabel_term(term, by=quality, label="Soro renomeado", reason="Teste de regeneração")
    second = generate("subdocument", approved_entry, "pdf", analyst).result
    assert second.content_hash == first.content_hash
    assert (first.same_as_first, second.same_as_first) == (True, True)
    assert second.file_hash != first.file_hash  # o selo muda a cada geração
    draft_content = content.build("subdocument", approved_entry, first.layout)
    assert draft_content["product"] == "PRODUTO RENOMEADO"  # o rascunho usaria o dado novo


@pytest.mark.req("006:FR-017")
def test_conteudo_diferente_na_regeneracao_gera_alerta(
    approved_entry, analyst, generate, seal_cert, monkeypatch, events
):
    generate("subdocument", approved_entry, "pdf", analyst)
    original = render_pdf.build_css
    monkeypatch.setattr(
        render_pdf, "build_css", lambda *a, **k: original(*a, **k) + " html { color: #010101; }"
    )
    second = generate("subdocument", approved_entry, "pdf", analyst).result
    assert second.same_as_first is False
    assert events("documents.regeneration_mismatch")


@pytest.mark.req("006:FR-017")
def test_aprovacao_anterior_a_006_e_congelada_na_primeira_geracao(
    complete_entry, analyst, manager, signing, generate, seal_cert, monkeypatch
):
    monkeypatch.setattr(content, "freeze", lambda *a, **k: None)
    signing.submit_and_approve("subdocument", complete_entry, analyst, manager)
    assert not FrozenRendering.objects.filter(object_id=complete_entry.pk).exists()
    monkeypatch.undo()
    doc = generate("subdocument", complete_entry, "pdf", analyst).result
    assert doc.official and FrozenRendering.objects.filter(object_id=complete_entry.pk).exists()
    assert services.lookup(doc.verification_code, user=analyst)["found"]
