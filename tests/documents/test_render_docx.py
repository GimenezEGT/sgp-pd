"""DOCX de conferência (FR-011, FR-015; research R11)."""

import copy
import datetime
import io
import zipfile

import pytest
from docx import Document

from sgp.documents import layouts, render_docx
from sgp.documents.preview import sample_content

pytestmark = [pytest.mark.django_db]
CREATED = datetime.datetime(2026, 11, 8, 10, 0)


@pytest.fixture
def layout(vocab_seed):
    return layouts.current_layout("subdocument")


@pytest.fixture
def data(vocab_seed):
    return sample_content("subdocument")


def _xml(docx: bytes, name: str) -> str:
    with zipfile.ZipFile(io.BytesIO(docx)) as archive:
        names = [n for n in archive.namelist() if n.startswith(name)]
        return "".join(archive.read(n).decode("utf-8") for n in names)


@pytest.mark.req("006:FR-008")
def test_pagina_a4_margens_rodape_e_cabecalho_de_tabela(layout, data):
    docx = render_docx.render(data, layout, draft=True, created=CREATED)
    section = Document(io.BytesIO(docx)).sections[0]
    assert round(section.page_width.cm, 1) == 21.0 and round(section.page_height.cm, 1) == 29.7
    assert round(section.left_margin.cm, 2) == 1.3 and round(section.top_margin.cm, 2) == 2.0
    footers = _xml(docx, "word/footer")
    assert 'w:instr="PAGE"' in footers and 'w:instr="NUMPAGES"' in footers
    assert "Formulário Versão: 05" in footers
    assert "w:tblHeader" in _xml(docx, "word/document.xml")


@pytest.mark.req("006:FR-011")
def test_rascunho_leva_marca_dagua_em_todas_as_paginas(layout, data):
    docx = render_docx.render(data, layout, draft=True, created=CREATED)
    headers = _xml(docx, "word/header")
    assert headers.count("RASCUNHO – NÃO VÁLIDO") >= 2  # cabeçalho da capa e das demais páginas
    assert "Cópia para conferência" not in _xml(docx, "word/footer")


@pytest.mark.req("006:FR-015")
def test_docx_de_versao_aprovada_e_copia_para_conferencia(layout, data):
    docx = render_docx.render(data, layout, draft=False, created=CREATED)
    assert "RASCUNHO" not in _xml(docx, "word/header")
    footers = _xml(docx, "word/footer")
    assert "Cópia para conferência – o documento oficial é o PDF" in footers
    assert "Código de verificação" not in footers


@pytest.mark.req("006:FR-017")
def test_mesmo_conteudo_gera_o_mesmo_docx(layout, data):
    first = render_docx.render(data, layout, draft=False, created=CREATED)
    assert first == render_docx.render(copy.deepcopy(data), layout, draft=False, created=CREATED)
    with zipfile.ZipFile(io.BytesIO(first)) as archive:
        assert {info.date_time for info in archive.infolist()} == {render_docx.ZIP_DATE}
