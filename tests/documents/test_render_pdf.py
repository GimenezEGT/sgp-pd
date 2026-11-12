"""PDF: capa, corpo, paginação, marca d'água, tabela longa, PDF/A e determinismo
(FR-004 a FR-011, SC-002, SC-004, SC-006, SC-007)."""

import copy
import io
import re
import time

import pytest
from pypdf import PdfReader

from sgp.documents import content, layouts, render_pdf
from sgp.documents.preview import sample_content
from tests.documents.conftest import flat, pdf_pages

pytestmark = [pytest.mark.django_db]
CREATED = "2026-11-08T10:00:00-03:00"


def render(data, layout, draft=True, code=""):
    return render_pdf.render(
        data, layout, draft=draft, created=CREATED, identifier=b"0" * 32, verification_code=code
    )


@pytest.fixture
def layout(vocab_seed):
    return layouts.current_layout("subdocument")


@pytest.fixture
def long_table(vocab_seed):
    data = sample_content("subdocument")
    table = data["sections"][0]["blocks"][2]
    table["rows"] = [[f"{i:03d}", f"Item fictício {i:03d}", f"{i},50"] for i in range(1, 121)]
    table["label"] = "Tabela longa de teste"
    return data


@pytest.mark.req("006:FR-004")
@pytest.mark.req("006:FR-008")
def test_capa_e_rodape_da_entrada(complete_entry, layout):
    pages = pdf_pages(render(content.build("subdocument", complete_entry, layout), layout))
    cover = flat(pages[0])
    for text in (
        "Entrada de Projeto",
        complete_entry.project.product_name.upper(),
        "VERSÃO",
        "ESTE RELATÓRIO DEVE CONTER:",
        "1 - Amostras",
        "13 - Outros dados pertinentes",
        "Analista Responsável (Nome/Função):",
        "Gestor de P&D:",
        "Data:",
        "Formulário Versão: 05. Referência: PSG 20 - Pesquisa e Desenvolvimento de Produtos",
    ):
        assert text in cover, text
    assert cover.index("Entrada de Projeto") < cover.index("ESTE RELATÓRIO") < cover.index("Data:")
    total = len(pages)
    for number, page in enumerate(pages, start=1):
        assert f"Página {number} de {total}" in flat(page)


@pytest.mark.req("006:FR-006")
@pytest.mark.req("006:FR-007")
def test_corpo_com_titulos_numerados_tabelas_e_nao_aplicavel(complete_entry, layout):
    body = flat(
        " ".join(
            pdf_pages(render(content.build("subdocument", complete_entry, layout), layout))[1:]
        )
    )
    assert "1. Amostras" in body and "13. Outros dados pertinentes" in body
    assert "Tabela 01 – " in body
    assert "Não aplicável. Método sem leitura óptica" in body


@pytest.mark.req("006:SC-002")
@pytest.mark.req("006:FR-007")
def test_tabela_de_120_linhas_repete_o_cabecalho_em_todas_as_paginas(long_table, layout):
    pages = pdf_pages(render(long_table, layout))
    with_rows = [flat(p) for p in pages if re.search(r"Item fictício \d{3}", p)]
    assert len(with_rows) >= 3
    for page in with_rows:
        assert "Nº Descrição Valor" in page
    assert "Item fictício 120" in with_rows[-1]


@pytest.mark.req("006:SC-004")
@pytest.mark.req("006:FR-011")
def test_marca_dagua_em_todas_as_paginas_do_rascunho_e_nenhuma_no_aprovado(long_table, layout):
    draft = pdf_pages(render(long_table, layout, draft=True))
    assert all("RASCUNHO – NÃO VÁLIDO" in flat(page) for page in draft)
    final = pdf_pages(render(long_table, layout, draft=False, code="ABCD-EFGH-JKMN-PQRS"))
    assert not any("RASCUNHO" in page for page in final)
    assert all("Código de verificação: ABCD-EFGH-JKMN-PQRS" in flat(page) for page in final)


@pytest.mark.req("006:FR-008")
def test_cabecalho_identifica_o_documento_a_partir_da_segunda_pagina(long_table, layout):
    pages = [flat(p) for p in pdf_pages(render(long_table, layout))]
    header = "Entrada de Projeto – NOME DO PRODUTO – Versão 01"
    assert header not in pages[0] and all(header in page for page in pages[1:])


@pytest.mark.req("006:SC-006")
def test_marcadores_de_pdf_a_2b(long_table, layout):
    data = render(long_table, layout, draft=False)
    reader = PdfReader(io.BytesIO(data))
    metadata = reader.trailer["/Root"]["/Metadata"].get_object().get_data().decode()
    assert 'pdfaid:part="2"' in metadata or "<pdfaid:part>2</pdfaid:part>" in metadata
    assert (
        'pdfaid:conformance="B"' in metadata
        or "<pdfaid:conformance>B</pdfaid:conformance>" in metadata
    )
    assert reader.trailer["/Root"]["/OutputIntents"]
    for page in reader.pages:
        resources = page["/Resources"]
        for font in resources.get("/Font", {}).values():
            descriptor = font.get_object()
            descendants = descriptor.get("/DescendantFonts")
            target = descendants[0].get_object() if descendants else descriptor
            fd = target["/FontDescriptor"].get_object()
            assert any(key in fd for key in ("/FontFile", "/FontFile2", "/FontFile3"))
        for image in resources.get("/XObject", {}).values():
            interpolate = image.get_object().get("/Interpolate")
            assert getattr(interpolate, "value", interpolate) in (None, False)


@pytest.mark.req("006:FR-017")
def test_mesmo_conteudo_gera_o_mesmo_pdf(long_table, layout):
    assert render(long_table, layout) == render(copy.deepcopy(long_table), layout)


@pytest.mark.req("006:FR-008")
def test_texto_com_caracteres_especiais_e_html_e_escapado(long_table, layout):
    long_table["product"] = 'KIT <b>"ÁCIDO" ≥ 5 µL ± 0,5 °C</b>'
    text = flat(" ".join(pdf_pages(render(long_table, layout))))
    assert 'KIT <b>"ÁCIDO" ≥ 5 µL ± 0,5 °C</b>' in text


@pytest.mark.req("006:SC-007")
def test_documento_de_30_paginas_em_menos_de_30_segundos(long_table, layout):
    table = long_table["sections"][0]["blocks"][2]
    table["rows"] = [[f"{i:04d}", f"Item fictício {i:04d}", f"{i},50"] for i in range(1, 1501)]
    start = time.perf_counter()
    pages = pdf_pages(render(long_table, layout))
    assert len(pages) >= 30
    assert time.perf_counter() - start < 30
