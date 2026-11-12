"""Gerar o documento completo: ordem, sumário, rascunho, oficial, reaproveitamento e acesso."""

import re

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse

from sgp.fulldoc import services
from sgp.fulldoc.models import FullDocument, RequestStatus

from .conftest import outline, pdf_text

EXPECTED_ORDER = [
    "Termo de Abertura do Projeto",
    "Plano de Negócios",
    "Entrada de Projeto",
    "Elaboração de Formulação",
    "Lote Piloto",
    "RAPD",
    "Análise Crítica",
    "Validação",
    "Verificação Final",
    "Saída",
    "Quadro de versões",
    "Resumo da trilha de auditoria",
    "Histórico do caderno de laboratório",
    "Lista de anexos",
]


def _flat(text: str) -> str:
    return " ".join(text.split())


@pytest.mark.req("009:FR-002")
@pytest.mark.req("009:FR-003")
@pytest.mark.req("009:FR-004")
@pytest.mark.req("009:SC-001")
def test_ordem_das_partes_e_sumario_com_as_paginas_reais(
    complete_project, run_fulldoc, document_bytes, seal_cert
):
    project = complete_project()
    done = run_fulldoc(project, project.leader)
    assert done.status == RequestStatus.DONE, done.error
    data = document_bytes(done.result)
    marks = outline(data)
    titles = [title for title, _ in marks]
    for expected, title in zip(EXPECTED_ORDER, titles, strict=True):
        assert title.startswith(expected) or expected.split()[0] in title, (expected, title)
    pages = pdf_text(data)
    toc = _flat(pages[1])
    assert toc.startswith("Sumário")
    for title, page in marks:
        found = re.search(re.escape(_flat(title)) + r"[ .]*?(\d+)", toc)
        assert found, title
        assert int(found.group(1)) == page, (title, found.group(1), page)
    total = len(pages)
    assert f"Página 1 de {total}" in _flat(pages[0]) or f"Página 2 de {total}" in _flat(pages[1])
    assert done.result.pages == total


@pytest.mark.req("009:FR-013")
@pytest.mark.req("009:FR-014")
def test_sem_pendencias_sai_oficial_com_selo_e_codigo(
    client, complete_project, run_fulldoc, document_bytes, seal_cert
):
    from sgp.documents import seal

    project = complete_project()
    done = run_fulldoc(project, project.leader)
    document = done.result
    assert document.official and document.pending == []
    assert re.fullmatch(
        r"[0-9A-Z]{4}-[0-9A-Z]{4}-[0-9A-Z]{4}-[0-9A-Z]{4}", document.verification_code
    )
    data = document_bytes(document)
    assert document.file_hash == document.file.sha256
    assert seal.validate(data, [seal_cert])["intact"]
    assert document.verification_code in _flat(" ".join(pdf_text(data)))
    client.force_login(project.leader)
    page = client.get(reverse("documents:verify"), {"codigo": document.verification_code})
    content = page.content.decode()
    assert "Documento completo do projeto" in content and "Código válido" in content


@pytest.mark.req("009:FR-013")
@pytest.mark.req("009:SC-002")
def test_com_pendencias_sai_rascunho_com_marca_e_lista(
    complete_project, run_fulldoc, document_bytes
):
    project = complete_project(rejected=True)
    done = run_fulldoc(project, project.leader)
    document = done.result
    assert not document.official and document.verification_code == ""
    assert len(document.pending) == 1
    pages = [_flat(page) for page in pdf_text(document_bytes(document))]
    assert "RASCUNHO" in pages[0] and "Rascunho" in pages[0]
    assert any(
        page.startswith("Pendências") or "Pendências O documento só é oficial" in page
        for page in pages
    )
    assert all("RASCUNHO" in page for page in pages)


@pytest.mark.req("009:FR-006")
@pytest.mark.req("009:FR-015")
def test_reaproveita_quando_nada_mudou_e_registra_os_eventos(
    complete_project, run_fulldoc, events, seal_cert
):
    project = complete_project()
    first = run_fulldoc(project, project.leader)
    second = run_fulldoc(project, project.leader)
    assert second.reused and second.result == first.result
    assert FullDocument.objects.filter(project=project).count() == 1
    third = run_fulldoc(project, project.leader, caderno="completo")
    assert not third.reused and third.result != first.result
    assert len(events("fulldoc.requested")) == 3
    assert len(events("fulldoc.generated")) == 2 and len(events("fulldoc.reused")) == 1
    assert second.progress == 100


@pytest.mark.req("009:FR-015")
def test_falha_fica_registrada_com_mensagem(complete_project, run_fulldoc, events, settings):
    settings.DOCUMENT_SEAL_PKCS12 = ""
    project = complete_project()
    done = run_fulldoc(project, project.leader)
    assert done.status == RequestStatus.FAILED and "certificado do selo" in done.error
    assert len(events("fulldoc.failed")) == 1


@pytest.mark.req("009:FR-001")
def test_quem_gera_e_um_pedido_ativo_por_projeto(signed_project, member, manager):
    with pytest.raises(PermissionDenied):
        services.request_document(signed_project, by=member, options={})
    first = services.request_document(signed_project, by=signed_project.leader, options={})
    assert first.status == RequestStatus.QUEUED
    with pytest.raises(ValidationError, match="sendo gerado"):
        services.request_document(signed_project, by=manager, options={})


@pytest.mark.req("009:FR-001")
@pytest.mark.req("009:FR-005")
def test_acesso_a_tela_e_ao_download(
    client, complete_project, run_fulldoc, member, make_user, events, seal_cert
):
    from sgp.accounts.profiles import Profile

    project = complete_project()
    with_financials = run_fulldoc(project, project.leader).result
    without = run_fulldoc(project, project.leader, omitir_financeiro=True).result
    assert with_financials.with_financials and not without.with_financials
    client.force_login(member)
    page = client.get(reverse("fulldoc:project", args=[project.pk])).content.decode()
    assert "Documentos gerados" in page and "Gerar o documento completo" not in page
    assert client.get(reverse("fulldoc:download", args=[without.pk])).status_code == 200
    assert client.get(reverse("fulldoc:download", args=[with_financials.pk])).status_code == 403
    assert (
        client.post(
            reverse("fulldoc:project", args=[project.pk]), {"caderno": "resumido"}
        ).status_code
        == 403
    )
    outsider = make_user(None, Profile.ANALYST)
    client.force_login(outsider)
    assert client.get(reverse("fulldoc:project", args=[project.pk])).status_code == 403
    assert client.get(reverse("fulldoc:download", args=[without.pk])).status_code == 403
    assert len(events("auth.permission_denied")) == 4
    assert len(events("fulldoc.downloaded")) == 1


@pytest.mark.req("009:FR-006")
def test_tela_pede_e_mostra_o_progresso(client, signed_project):
    client.force_login(signed_project.leader)
    url = reverse("fulldoc:project", args=[signed_project.pk])
    response = client.post(url, {"caderno": "resumido"})
    assert response.status_code == 302
    page = client.get(url).content.decode()
    assert "Último pedido" in page and 'hx-trigger="every 2s"' in page and "Pendências" in page
