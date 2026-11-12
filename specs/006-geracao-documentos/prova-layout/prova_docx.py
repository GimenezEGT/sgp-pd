"""Abordagem (a): modelo Word com docxtpl e conversão para PDF/A-2b pelo LibreOffice headless."""

import hashlib
import json
import subprocess
import sys
import time

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from docxtpl import DocxTemplate

import dados

DASH = chr(0x2013)


def run(par, text, size=None, bold=False):
    r = par.add_run(text)
    if size:
        r.font.size = Pt(size)
    r.bold = bold
    return r


def field(par, instr, placeholder):
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), instr)
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = placeholder
    r.append(t)
    fld.append(r)
    par._p.append(fld)


def no_borders(table):
    tblPr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"), "nil")
        borders.append(el)
    tblPr.append(borders)


def shade(cell, color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tcPr.append(shd)


def build_template(path):
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(1.3)
    sec.top_margin = sec.bottom_margin = Cm(2.0)
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    normal.paragraph_format.space_after = Pt(0)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture("/logo/logo-bioclin-quibasa.png", width=Cm(12.84))
    p.paragraph_format.space_after = Pt(30)
    for text, size, bold, upper, after in (
        ("{{ titulo }}", 24, True, False, 16),
        ("{{ produto|upper }}", 20, True, False, 10),
        ("VERSÃO {{ versao }}", 20, False, False, 30),
    ):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(after)
        run(p, text, size, bold)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(10)
    run(p, "ESTE RELATÓRIO DEVE CONTER:", 16, True)

    cols = doc.add_table(rows=1, cols=2)
    no_borders(cols)
    for idx, name in enumerate(("col1", "col2")):
        cell = cols.rows[0].cells[idx]
        cell.paragraphs[0].text = "{%p for n, t in " + name + " %}"
        item = cell.add_paragraph()
        item.paragraph_format.space_after = Pt(6)
        run(item, "{{ n }} - {{ t }}", 14)
        cell.add_paragraph("{%p endfor %}")
    gap = doc.add_paragraph()
    gap.paragraph_format.space_after = Pt(36)
    for label in ("Analista Responsável (Nome/Função):", "Gestor de P&D:"):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(14)
        run(p, label, 12, True)
        run(p, " ________________________________", 12)
    p = doc.add_paragraph()
    run(p, "Data: ____", 12, True)
    doc.add_page_break()

    h = doc.add_paragraph()
    h.paragraph_format.space_after = Pt(6)
    run(h, "1. Amostras", 12, True)
    doc.add_paragraph("Texto de exemplo do tópico, gerado a partir de dados fictícios.")
    t = doc.add_paragraph()
    t.paragraph_format.space_before = Pt(8)
    run(t, f"Tabela 01 {DASH} Itens de teste fictícios", 11, True)

    table = doc.add_table(rows=4, cols=len(dados.COLUNAS))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    header = table.rows[0]
    trPr = header._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    trPr.append(th)
    for i, name in enumerate(dados.COLUNAS):
        header.cells[i].paragraphs[0].text = ""
        run(header.cells[i].paragraphs[0], name, 10, True)
        shade(header.cells[i], "D9D9D9")
    table.rows[1].cells[0].paragraphs[0].text = "{%tr for r in linhas %}"
    for i in range(len(dados.COLUNAS)):
        table.rows[2].cells[i].paragraphs[0].text = ""
        run(table.rows[2].cells[i].paragraphs[0], "{{ r[%d] }}" % i, 10)
    table.rows[3].cells[0].paragraphs[0].text = "{%tr endfor %}"

    foot = sec.footer.paragraphs[0]
    foot.paragraph_format.tab_stops.add_tab_stop(Cm(18.4), WD_TAB_ALIGNMENT.RIGHT)
    run(foot, "Formulário Versão: {{ form_versao }}. Referência: {{ referencia }}\tPágina ", 11)
    field(foot, "PAGE", "1")
    run(foot, " de ", 11)
    field(foot, "NUMPAGES", "1")
    doc.save(path)


def main():
    out_pdf = sys.argv[1]
    rascunho = len(sys.argv) > 2 and sys.argv[2] == "rascunho"
    t0 = time.perf_counter()
    build_template("modelo.docx")
    col1, col2 = dados.colunas_capa()
    tpl = DocxTemplate("modelo.docx")
    tpl.render(
        {
            "titulo": dados.TITULO,
            "produto": dados.PRODUTO,
            "versao": dados.VERSAO,
            "form_versao": dados.FORM_VERSAO,
            "referencia": dados.REFERENCIA,
            "col1": col1,
            "col2": col2,
            "linhas": dados.linhas(),
        }
    )
    tpl.save("saida.docx")
    t1 = time.perf_counter()
    options = {"SelectPdfVersion": {"type": "long", "value": "2"}}
    if rascunho:
        options["Watermark"] = {"type": "string", "value": f"RASCUNHO {DASH} NÃO VÁLIDO"}
    subprocess.run(
        [
            "soffice",
            "--headless",
            "--convert-to",
            "pdf:writer_pdf_Export:" + json.dumps(options),
            "--outdir",
            "lo",
            "saida.docx",
        ],
        check=True,
        capture_output=True,
    )
    t2 = time.perf_counter()
    pdf = open("lo/saida.pdf", "rb").read()
    open(out_pdf, "wb").write(pdf)
    print(
        f"docx {out_pdf}: {len(pdf)} bytes, docxtpl {t1 - t0:.2f}s, soffice {t2 - t1:.2f}s, "
        f"sha256={hashlib.sha256(pdf).hexdigest()[:16]}"
    )


if __name__ == "__main__":
    main()
