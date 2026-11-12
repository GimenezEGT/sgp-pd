"""Geração em PDF e DOCX, rascunho e final, pacote, declaração e acesso (FR-004 a FR-007, FR-010, FR-013)."""

import io
import zipfile

import pytest
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from docx import Document

from sgp.dossier import services
from sgp.files.storage import read_verified

from .conftest import pdf_text

ROMAN_TITLES = [
    "I. DESCRIÇÃO DO PRODUTO",
    "II. IMAGEM DO PRODUTO",
    "III. GERENCIAMENTO DE RISCO",
    "IV. NORMAS TÉCNICAS",
    "V. CERTIFICADO DE CONFORMIDADE",
    "VI. ESTUDO DE DESEMPENHO",
    "VII. ESTUDO DE ESTABILIDADE",
    "VIII. DESEMPENHO CLÍNICO",
    "IX. ROTULAGEM E INSTRUÇÃO DE USO",
    "X. UNIDADE FABRIL",
    "XI. PROCESSO DE FABRICAÇÃO",
    "XII. REFERÊNCIAS BIBLIOGRÁFICAS",
]


def _final(signed_project, approved_entry_with_class, quality, approved_text):
    approved_entry_with_class("II")
    approved_text()
    services.save_supplement(
        signed_project,
        by=quality,
        item_key="I.B",
        text="Analito fictício do KIT DE TESTE.",
        not_applicable=False,
        justification="",
    )
    return services.generate(signed_project, by=quality)


@pytest.mark.req("011:FR-004")
@pytest.mark.req("011:SC-003")
def test_arvore_de_titulos_i_a_xii_no_pdf_e_no_docx(
    signed_project, approved_entry_with_class, quality, company
):
    approved_entry_with_class("II")
    version = services.generate(signed_project, by=quality)
    assert not version.final
    text = pdf_text(read_verified(version.pdf))
    body = text.index("I. DESCRIÇÃO DO PRODUTO A. Finalidade (Indicação de Uso)")
    positions = [text.find(title, body) for title in ROMAN_TITLES]
    assert all(p >= 0 for p in positions) and positions == sorted(positions), positions
    assert (
        "Dossiê Técnico KIT DE TESTE" in text and "Empresa Fictícia de Diagnósticos Ltda." in text
    )
    assert "RASCUNHO" in text and "Pendências para o dossiê final" in text
    assert "A. Finalidade (Indicação de Uso)" in text and "1. Analito" in text
    document = Document(io.BytesIO(read_verified(version.docx)))
    headings = [p.text for p in document.paragraphs if p.style.name.startswith("Heading 1")]
    assert [h for h in headings if h != "ANEXOS"] == ROMAN_TITLES[:4] + [
        "V. CERTIFICADO DE CONFORMIDADE (INSTRUMENTOS DE CERTIFICAÇÃO COMPULSÓRIA)"
    ] + ROMAN_TITLES[5:]
    header = document.sections[0].header.paragraphs[0]
    assert header.text == "Dossiê Técnico KIT DE TESTE" and header.runs[0].italic


@pytest.mark.req("011:FR-005")
@pytest.mark.req("011:SC-001")
def test_item_faltando_impede_o_final(
    signed_project, approved_entry_with_class, quality, company, minimal_definition
):
    approved_entry_with_class("II")
    version = services.generate(signed_project, by=quality)
    assert not version.final and version.package is None
    missing = [row["item"] for row in version.checklist if row["situacao"] == "missing"]
    assert missing == ["I.B", "V"]


@pytest.mark.req("011:FR-006")
@pytest.mark.req("011:FR-007")
@pytest.mark.req("011:FR-010")
def test_final_com_pacote_declaracao_e_italico(
    signed_project,
    approved_entry_with_class,
    quality,
    company,
    minimal_definition,
    approved_text,
    events,
):
    version = _final(signed_project, approved_entry_with_class, quality, approved_text)
    assert version.final and version.risk_class == "II" and len(version.content_hash) == 64
    text = pdf_text(read_verified(version.pdf))
    assert (
        "O abaixo assinado Pessoa Responsável Fictícia, inscrito no Conselho Regional de Farmácia de MG sob nº 00000"
        in text
    )
    assert "Responsável Técnico e Legal" in text and "Ver Anexo 01 – matriz-risco.pdf" in text
    assert (
        "RASCUNHO" not in text and "Não aplicável. Exigido apenas para as classes III e IV." in text
    )
    archive = zipfile.ZipFile(io.BytesIO(read_verified(version.package)))
    names = archive.namelist()
    assert any(n.endswith(".pdf") and n.startswith("Dossie") for n in names)
    assert "anexos/Anexo 01 - matriz-risco.pdf" in names
    document = Document(io.BytesIO(read_verified(version.docx)))
    italic = [run.text for p in document.paragraphs for run in p.runs if run.italic]
    assert "KIT DE TESTE" in italic
    assert version.texts_used == {"unidade-fabril": 1}
    assert events("dossier.generated")[-1].new_value["final"] is True


@pytest.mark.req("011:FR-004")
def test_tabelas_numeradas_no_dossie(signed_project, approved_entry_with_class, quality, company):
    services.publish_definition(
        by=quality,
        text="itens: [{numero: I, titulo: Apresentação, fontes: [{tipo: subdocumento, subdocumento: entrada, topico: apresentacoes}]}]",
    )
    approved_entry_with_class("II")
    text = pdf_text(read_verified(services.generate(signed_project, by=quality).pdf))
    assert "Tabela 01 –" in text


@pytest.mark.req("011:FR-013")
def test_permissoes(
    client, signed_project, approved_entry_with_class, member, quality, make_user, events
):
    from sgp.accounts.profiles import Profile

    approved_entry_with_class("II")
    with pytest.raises(PermissionDenied):
        services.generate(signed_project, by=member)
    version = services.generate(signed_project, by=quality)
    client.force_login(member)
    assert client.get(reverse("dossier:project", args=[signed_project.pk])).status_code == 200
    assert client.post(reverse("dossier:project", args=[signed_project.pk])).status_code == 403
    assert client.get(reverse("dossier:download", args=[version.pk, "pdf"])).status_code == 200
    client.force_login(make_user(None, Profile.ANALYST))
    assert client.get(reverse("dossier:project", args=[signed_project.pk])).status_code == 403
    assert client.get(reverse("dossier:download", args=[version.pk, "pdf"])).status_code == 403
    assert len(events("dossier.downloaded")) == 1
