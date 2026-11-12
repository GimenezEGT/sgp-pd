"""Pedido, geração em segundo plano, arquivo, histórico e download (FR-001 a FR-003, FR-016,
FR-018, FR-025)."""

import hashlib

import pytest
from django.core.exceptions import PermissionDenied
from django.urls import reverse

from sgp.accounts.profiles import Profile
from sgp.documents import services
from sgp.documents.models import GeneratedDocument, GenerationRequest
from sgp.files.storage import media_root
from sgp.projects.models import Project

pytestmark = [pytest.mark.django_db]


@pytest.mark.req("006:FR-001")
@pytest.mark.req("006:FR-016")
def test_rascunho_gerado_e_arquivado_com_resumos(
    complete_entry, analyst, generate, file_bytes, events
):
    pending = generate("subdocument", complete_entry, "pdf", analyst)
    assert pending.status == "done" and pending.official is False
    doc = pending.result
    data = file_bytes(doc)
    assert data.startswith(b"%PDF-")
    assert doc.file_hash == hashlib.sha256(data).hexdigest() == doc.content_hash
    assert (doc.version, doc.document_status, doc.format) == (1, "draft", "pdf")
    assert doc.form_template_id == complete_entry.template_id and doc.layout.version == 1
    assert doc.data_version == complete_entry.row_version
    assert doc.verification_code == "" and doc.generated_by == analyst
    generated = events("documents.generated")[-1]
    assert generated.new_value["resumo_arquivo"] == doc.file_hash
    assert events("documents.requested")


@pytest.mark.req("006:FR-001")
def test_docx_gerado_e_arquivado(complete_entry, analyst, generate, file_bytes):
    doc = generate("subdocument", complete_entry, "docx", analyst).result
    assert doc.format == "docx" and file_bytes(doc).startswith(bytes([0x50, 0x4B]))
    assert doc.file.content_type.endswith("wordprocessingml.document")


@pytest.mark.req("006:FR-002")
def test_pedido_em_andamento_e_reaproveitado(complete_entry, analyst):
    first = services.request_generation("subdocument", complete_entry, "pdf", by=analyst)
    again = services.request_generation("subdocument", complete_entry, "pdf", by=analyst)
    assert first.pk == again.pk and first.status == "queued"
    other = services.request_generation("subdocument", complete_entry, "docx", by=analyst)
    assert other.pk != first.pk
    services.run_request(first.pk)
    assert GenerationRequest.objects.get(pk=first.pk).status == "done"
    services.run_request(first.pk)  # pedido já concluído não roda de novo
    assert GeneratedDocument.objects.filter(format="pdf").count() == 1


@pytest.mark.req("006:FR-003")
def test_quem_nao_ve_o_documento_nao_gera_nem_baixa(
    complete_entry, analyst, generate, make_user, client, events
):
    outsider = make_user(None, Profile.ANALYST)
    with pytest.raises(PermissionDenied):
        services.request_generation("subdocument", complete_entry, "pdf", by=outsider)
    doc = generate("subdocument", complete_entry, "pdf", analyst).result
    client.force_login(outsider)
    urls = [
        reverse("documents:history", args=["subdocument", complete_entry.pk]),
        reverse("documents:download", args=[doc.pk]),
    ]
    for url in urls:
        assert client.get(url).status_code == 403
    assert (
        client.post(
            reverse("documents:generate", args=["subdocument", complete_entry.pk]),
            {"formato": "pdf"},
        ).status_code
        == 403
    )
    assert len(events("auth.permission_denied")) == 3


@pytest.mark.req("006:FR-002")
@pytest.mark.req("006:FR-025")
def test_falha_fica_visivel_registrada_e_sem_arquivo(complete_entry, analyst, monkeypatch, events):
    from sgp.documents import render_pdf

    def broken(*args, **kwargs):
        raise RuntimeError("falha simulada")

    monkeypatch.setattr(render_pdf, "render", broken)
    pending = services.request_generation("subdocument", complete_entry, "pdf", by=analyst)
    pending = services.run_request(pending.pk)
    assert pending.status == "failed" and "Falha inesperada" in pending.error
    assert GeneratedDocument.objects.count() == 0
    failed = events("documents.generation_failed")[-1]
    assert failed.new_value["pedido"] == pending.pk


@pytest.mark.req("006:FR-002")
@pytest.mark.req("006:FR-018")
def test_telas_de_pedido_historico_e_download(
    complete_entry, analyst, client, events, django_capture_on_commit_callbacks
):
    client.force_login(analyst)
    url = reverse("documents:generate", args=["subdocument", complete_entry.pk])
    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(url, {"formato": "pdf"}, HTTP_HX_REQUEST="true")
    assert response.status_code == 200 and "pedido-" in response.content.decode()
    pending = GenerationRequest.objects.get()
    assert pending.status == "done"  # Celery síncrono nos testes
    status = client.get(reverse("documents:request", args=[pending.pk])).content.decode()
    assert "Baixar o arquivo" in status and "hx-trigger" not in status
    page = client.get(reverse("documents:history", args=["subdocument", complete_entry.pk]))
    text = page.content.decode()
    assert "Histórico de gerações" in text and pending.result.content_hash[:16] in text
    download = client.get(reverse("documents:download", args=[pending.result.pk]))
    assert download.status_code == 200 and download["Content-Type"] == "application/pdf"
    assert "attachment" in download["Content-Disposition"]
    assert events("documents.downloaded")[-1].new_value["arquivo"] == pending.result.file_id


@pytest.mark.req("006:FR-016")
def test_arquivo_alterado_fora_do_sistema_nao_e_entregue(
    complete_entry, analyst, generate, client, events
):
    doc = generate("subdocument", complete_entry, "pdf", analyst).result
    (media_root() / doc.file.storage_name).write_bytes(b"%PDF-adulterado")
    client.force_login(analyst)
    response = client.get(reverse("documents:download", args=[doc.pk]))
    assert response.status_code == 409
    assert events("files.integrity_failed") and not events("documents.downloaded")


@pytest.mark.req("006:FR-001")
def test_projeto_fora_de_execucao_continua_gerando_para_quem_tem_acesso(
    complete_entry, manager, generate
):
    Project.objects.filter(pk=complete_entry.project_id).update(status="returned")
    assert generate("subdocument", complete_entry, "pdf", manager).status == "done"


@pytest.mark.req("006:FR-002")
def test_documento_que_mudou_de_versao_depois_do_pedido_falha_com_mensagem(
    approved_entry, analyst, manager
):
    from sgp.signatures import services as signatures

    pending = services.request_generation("subdocument", approved_entry, "docx", by=analyst)
    signatures.new_version("subdocument", approved_entry, by=analyst, reason="Correção")
    pending = services.run_request(pending.pk)
    assert pending.status == "failed" and "mudou de versão" in pending.error
