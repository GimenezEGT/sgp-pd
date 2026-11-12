"""DOCX de conferência (python-docx) a partir do mesmo conteúdo e layout do PDF (research R11).

Nunca é documento oficial (FR-015): sem selo nem código; versão não aprovada leva a marca d'água
e a aprovada, a indicação de cópia para conferência. O ZIP sai normalizado (datas fixas), para que
o mesmo conteúdo gere o mesmo arquivo.
"""

import io
import zipfile
from xml.sax.saxutils import quoteattr

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from . import layouts
from .layout_schema import fill
from .render_pdf import (
    BLANK_DATE,
    BLANK_LINE,
    DASH,
    cover_columns,
    cover_signatures,
    footer_lines,
    placeholders_for,
    signature_line,
)

CONFERENCE_NOTE = f"Cópia para conferência {DASH} o documento oficial é o PDF"
ZIP_DATE = (1980, 1, 1, 0, 0, 0)
CHECKED, UNCHECKED = chr(0x2612), chr(0x2610)
TWIPS_PER_CM = 567
PAGE_WIDTH_CM = 21.0

WATERMARK_XML = (
    '<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">'
    "<w:pict>"
    '<v:shapetype id="_x0000_t136" coordsize="21600,21600" o:spt="136" adj="10800" '
    'path="m@7,l@8,m@5,21600l@6,21600e">'
    "<v:formulas>"
    '<v:f eqn="sum #0 0 10800"/><v:f eqn="prod #0 2 1"/><v:f eqn="sum 21600 0 @1"/>'
    '<v:f eqn="sum 0 0 @2"/><v:f eqn="sum 21600 0 @3"/><v:f eqn="if @0 @3 0"/>'
    '<v:f eqn="if @0 21600 @1"/><v:f eqn="if @0 0 @2"/><v:f eqn="if @0 @4 21600"/>'
    '<v:f eqn="mid @5 @6"/><v:f eqn="mid @8 @5"/><v:f eqn="mid @7 @8"/>'
    '<v:f eqn="mid @6 @7"/><v:f eqn="sum @6 0 @5"/>'
    "</v:formulas>"
    '<v:path textpathok="t" o:connecttype="custom" '
    'o:connectlocs="@9,0;@10,10800;@11,21600;@12,10800" o:connectangles="270,180,90,0"/>'
    '<v:textpath on="t" fitshape="t"/>'
    '<v:handles><v:h position="#0,bottomRight" xrange="6629,14971"/></v:handles>'
    '<o:lock v:ext="edit" text="t" shapetype="t"/>'
    "</v:shapetype>"
    '<v:shape id="SGPMarcaDagua" o:spid="_x0000_s2049" type="#_x0000_t136" '
    'style="position:absolute;margin-left:0;margin-top:0;width:468pt;height:78pt;rotation:315;'
    "z-index:-251654144;mso-position-horizontal:center;mso-position-horizontal-relative:margin;"
    'mso-position-vertical:center;mso-position-vertical-relative:margin" '
    'o:allowincell="f" fillcolor={color} stroked="f">'
    '<v:fill opacity=".5"/>'
    '<v:textpath style="font-family:&quot;Calibri&quot;;font-size:1pt" string={text}/>'
    "</v:shape>"
    "</w:pict></w:r>"
)


def _run(paragraph, text: str, size=None, bold=False, italic=False):
    run = paragraph.add_run(text)
    if size:
        run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    return run


def _paragraph(container, text="", *, size=None, bold=False, align=None, before=0, after=4):
    paragraph = container.add_paragraph()
    if text:
        _run(paragraph, text, size, bold)
    if align is not None:
        paragraph.alignment = align
    paragraph.paragraph_format.space_before = Pt(before)
    paragraph.paragraph_format.space_after = Pt(after)
    return paragraph


def _field(paragraph, instruction: str, placeholder: str, size) -> None:
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), instruction)
    run = OxmlElement("w:r")
    props = OxmlElement("w:rPr")
    size_el = OxmlElement("w:sz")
    size_el.set(qn("w:val"), str(int(size * 2)))
    props.append(size_el)
    run.append(props)
    text = OxmlElement("w:t")
    text.text = placeholder
    run.append(text)
    field.append(run)
    paragraph._p.append(field)


def _no_borders(table) -> None:
    borders = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{side}")
        element.set(qn("w:val"), "nil")
        borders.append(element)
    table._tbl.tblPr.append(borders)


def _indent(table, cm: float) -> None:
    indent = OxmlElement("w:tblInd")
    indent.set(qn("w:w"), str(int(cm * TWIPS_PER_CM)))
    indent.set(qn("w:type"), "dxa")
    table._tbl.tblPr.append(indent)


def _repeat_header(row) -> None:
    header = OxmlElement("w:tblHeader")
    header.set(qn("w:val"), "true")
    row._tr.get_or_add_trPr().append(header)


def _shade(cell, color: str) -> None:
    shading = OxmlElement("w:shd")
    shading.set(qn("w:val"), "clear")
    shading.set(qn("w:color"), "auto")
    shading.set(qn("w:fill"), color.lstrip("#"))
    cell._tc.get_or_add_tcPr().append(shading)


def _cell_text(cell, text: str, size, bold=False) -> None:
    lines = (text or "").split("\n")
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_after = Pt(0)
    for index, line in enumerate(lines):
        run = _run(paragraph, line, size, bold)
        if index < len(lines) - 1:
            run.add_break()


def _data_table(doc, columns, rows, totals, definition, *, header_rows=None):
    size = definition["body"]["table_pt"]
    fill_color = definition["body"]["table_header_fill"]
    table = doc.add_table(rows=1, cols=len(columns))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for row in header_rows or []:
        cells = table.rows[0].cells
        merged = cells[0].merge(cells[-1]) if len(cells) > 1 else cells[0]
        _cell_text(merged, row, size, bold=True)
        merged.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        _repeat_header(table.rows[0])
        table.add_row()
    header = table.rows[-1]
    _repeat_header(header)
    for index, column in enumerate(columns):
        _cell_text(header.cells[index], column, size, bold=True)
        _shade(header.cells[index], fill_color)
    for values in rows:
        cells = table.add_row().cells
        for index, value in enumerate(values):
            _cell_text(cells[index], value, size)
    if totals:
        cells = table.add_row().cells
        for index, value in enumerate(totals):
            _cell_text(cells[index], value, size, bold=True)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def _block(doc, block: dict, definition: dict) -> None:
    kind = block["kind"]
    if kind == "values":
        lines = block["lines"]
        if block["label"] and len(lines) == 1:
            paragraph = _paragraph(doc)
            _run(paragraph, f"{block['label']}: ", bold=True)
            _run(paragraph, lines[0])
            return
        if block["label"]:
            _paragraph(doc, f"{block['label']}:", bold=True, after=2)
        if len(lines) == 1:
            _paragraph(doc, lines[0])
        for line in lines if len(lines) > 1 else []:
            doc.add_paragraph(line, style="List Bullet")
        if not lines:
            _paragraph(doc, DASH)
    elif kind == "rich":
        if block["label"]:
            _paragraph(doc, f"{block['label']}:", bold=True, after=2)
        for item in block["items"]:
            if "ul" in item:
                for line in item["ul"]:
                    doc.add_paragraph(line, style="List Bullet")
            else:
                paragraph = _paragraph(doc)
                lines = item["p"].split("\n")
                for index, line in enumerate(lines):
                    run = _run(paragraph, line)
                    if index < len(lines) - 1:
                        run.add_break()
    elif kind == "table":
        if not block["rows"]:
            paragraph = _paragraph(doc)
            _run(paragraph, f"{block['label']}: ", bold=True)
            _run(paragraph, DASH)
            return
        title = _paragraph(doc, f"{block['number']} {DASH} {block['label']}", bold=True, before=6)
        title.paragraph_format.keep_with_next = True
        _data_table(doc, block["columns"], block["rows"], block["totals"], definition)
        for note in block["notes"]:
            _paragraph(doc, note, size=definition["body"]["table_pt"] - 1)
    elif kind == "files":
        _paragraph(doc, f"{block['label']}:", bold=True, after=2)
        for item in block["files"]:
            doc.add_paragraph(f"{item['name']} (SHA-256: {item['sha256']})", style="List Bullet")
    elif kind == "note":
        paragraph = _paragraph(doc)
        _run(paragraph, block["text"], italic=True)
    elif kind == "empty":
        paragraph = _paragraph(doc)
        _run(paragraph, f"{block['label']}: ", bold=True)
        _run(paragraph, block["text"], italic=True)


def _borderless(doc, columns: list[list[str]], *, indent_cm, first_width_cm, size):
    table = doc.add_table(rows=1, cols=len(columns))
    _no_borders(table)
    _indent(table, indent_cm)
    for index, column in enumerate(columns):
        cell = table.rows[0].cells[index]
        if index == 0 and len(columns) > 1:
            cell.width = Cm(first_width_cm)
        for line_index, line in enumerate(column):
            paragraph = cell.paragraphs[0] if line_index == 0 else cell.add_paragraph()
            paragraph.paragraph_format.space_after = Pt(6)
            _run(paragraph, line, size)
    return table


def _cover(doc, content: dict, definition: dict, logo: bytes) -> None:
    cover = definition["cover"]
    indent = Cm(cover["indent_cm"])
    title_pt = cover.get("title_pt_by_type", {}).get(content.get("type"), cover["title_pt"])
    topics_pt = cover.get("topics_pt_by_type", {}).get(content.get("type"), cover["topics_pt"])
    paragraph = _paragraph(doc, align=WD_ALIGN_PARAGRAPH.CENTER, before=17, after=55)
    paragraph.add_run().add_picture(
        io.BytesIO(logo),
        width=Cm(definition["logo"]["width_cm"]),
        height=Cm(definition["logo"]["height_cm"]),
    )
    center = WD_ALIGN_PARAGRAPH.CENTER
    _paragraph(doc, content["title"], size=title_pt, bold=True, align=center, after=13)
    _paragraph(doc, content["product"], size=cover["product_pt"], bold=True, align=center, after=13)
    if content.get("changed_version"):
        version = (
            f"Versão alterada: {content['changed_version']}    "
            f"Nova Versão: {content['new_version']}"
        )
    else:
        version = f"VERSÃO    {content['version']}"
    _paragraph(doc, version, size=cover["version_pt"], align=center, after=30)
    checklist = content["cover"].get("checklist")
    if checklist:
        _data_table(
            doc,
            checklist["columns"],
            checklist["rows"],
            None,
            definition,
            header_rows=[checklist["title"]],
        )
    elif content["cover"]["topics"]:
        paragraph = _paragraph(
            doc, "ESTE RELATÓRIO DEVE CONTER:", size=cover["contains_pt"], bold=True, after=21
        )
        paragraph.paragraph_format.left_indent = indent
        columns = [[f"{n} - {label}" for n, label in column] for column in cover_columns(content)]
        _borderless(
            doc,
            columns,
            indent_cm=cover["indent_cm"],
            first_width_cm=cover["second_column_cm"],
            size=topics_pt,
        )
    sectors = content["cover"].get("sectors")
    if sectors:
        columns = [
            [f"{CHECKED if s['checked'] else UNCHECKED}  {s['label']}" for s in column]
            for column in sectors["columns"]
        ]
        _borderless(
            doc,
            columns,
            indent_cm=cover["indent_cm"],
            first_width_cm=7,
            size=topics_pt,
        )
    author, approver = cover_signatures(content)
    size = cover["signature_pt"]
    rows = [
        (content["cover"]["author_label"], signature_line(author) or BLANK_LINE),
        (content["cover"]["approver_label"], signature_line(approver) or BLANK_LINE),
    ]
    first = True
    for label, line in rows:
        paragraph = _paragraph(doc, label, size=size, bold=True, before=45 if first else 0, after=1)
        paragraph.paragraph_format.left_indent = indent
        paragraph.paragraph_format.keep_with_next = True
        paragraph = _paragraph(doc, line, size=size, after=13)
        paragraph.paragraph_format.left_indent = indent
        paragraph.paragraph_format.keep_with_next = True
        first = False
    paragraph = _paragraph(
        doc, f"Data: {content['approved_on'] or BLANK_DATE}", size=size, bold=True
    )
    paragraph.paragraph_format.left_indent = indent
    paragraph.add_run().add_break(WD_BREAK.PAGE)


def _watermark(paragraph, definition: dict) -> None:
    xml = WATERMARK_XML.format(
        color=quoteattr(definition["watermark"]["color"]),
        text=quoteattr(definition["watermark"]["text"]),
    )
    paragraph._p.append(parse_xml(xml))


def _footer(footer, lines: list[str], definition: dict) -> None:
    size = definition["footer"]["pt"]
    width = (
        PAGE_WIDTH_CM - definition["page"]["margin_left_cm"] - definition["page"]["margin_right_cm"]
    )
    paragraph = footer.paragraphs[0]
    paragraph.paragraph_format.tab_stops.add_tab_stop(Cm(width), WD_TAB_ALIGNMENT.RIGHT)
    _run(paragraph, (lines[0] if lines else "") + "\tPágina ", size)
    _field(paragraph, "PAGE", "1", size)
    _run(paragraph, " de ", size)
    _field(paragraph, "NUMPAGES", "1", size)
    for line in lines[1:]:
        extra = footer.add_paragraph()
        _run(extra, line, size)


def render(content: dict, layout, *, draft: bool, created) -> bytes:
    definition = layout.definition
    doc = Document()
    section = doc.sections[0]
    page = definition["page"]
    section.page_width, section.page_height = Cm(PAGE_WIDTH_CM), Cm(29.7)
    section.top_margin, section.bottom_margin = (
        Cm(page["margin_top_cm"]),
        Cm(page["margin_bottom_cm"]),
    )
    section.left_margin, section.right_margin = (
        Cm(page["margin_left_cm"]),
        Cm(page["margin_right_cm"]),
    )
    section.different_first_page_header_footer = True
    normal = doc.styles["Normal"]
    normal.font.name = definition["font"]["family"]
    normal.font.size = Pt(definition["font"]["body_pt"])
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), definition["font"]["family"])
    normal.paragraph_format.space_after = Pt(4)

    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _run(
        header,
        fill(definition["header"]["text"], placeholders_for(content)),
        definition["header"]["pt"],
    )
    if draft:
        _watermark(header, definition)
        _watermark(section.first_page_header.paragraphs[0], definition)
    lines = footer_lines(content, definition, extra="" if draft else CONFERENCE_NOTE)
    _footer(section.footer, lines, definition)
    _footer(section.first_page_footer, lines, definition)

    _cover(doc, content, definition, layouts.logo_bytes(layout))
    for item in content["sections"]:
        heading = _paragraph(
            doc,
            f"{item['number']}. {item['label']}",
            size=definition["body"]["heading_pt"],
            bold=True,
            before=10,
            after=4,
        )
        heading.paragraph_format.keep_with_next = True
        if item["not_applicable"]:
            _paragraph(doc, f"Não aplicável. {item['justification']}")
        for block in item["blocks"]:
            _block(doc, block, definition)
    form = content.get("optional_form")
    if form:
        doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        _paragraph(doc, form["title"], size=definition["body"]["heading_pt"], bold=True)
        for line in form["lines"]:
            _paragraph(doc, line)
        for group in form["groups"]:
            _paragraph(doc, group["label"], bold=True, after=2)
            _paragraph(
                doc,
                "    ".join(
                    f"{CHECKED if option['checked'] else UNCHECKED} {option['label']}"
                    for option in group["options"]
                ),
            )
        if form["note"]:
            paragraph = _paragraph(doc)
            _run(paragraph, form["note"], italic=True)
    if content.get("signatures"):
        _paragraph(
            doc,
            "Registro de assinaturas eletrônicas",
            size=definition["body"]["heading_pt"],
            bold=True,
            before=10,
        )
        _data_table(
            doc,
            ["Significado", "Nome", "Função", "Data e hora", "Delegação"],
            [
                [s["meaning"], s["name"], s["title"], s["at"], s["delegation"]]
                for s in content["signatures"]
            ],
            None,
            definition,
        )
    properties = doc.core_properties
    properties.author = "SGP-P&D"
    properties.last_modified_by = "SGP-P&D"
    properties.title = (
        f"{content['title']} {DASH} {content['product']} {DASH} Versão {content['version']}"
    )
    properties.created = created
    properties.modified = created
    properties.revision = 1
    buffer = io.BytesIO()
    doc.save(buffer)
    return normalize(buffer.getvalue())


def normalize(data: bytes) -> bytes:
    """Mesmo conteúdo, mesmo arquivo: entradas do ZIP com data fixa e na mesma ordem."""
    source = zipfile.ZipFile(io.BytesIO(data))
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as target:
        for info in source.infolist():
            entry = zipfile.ZipInfo(info.filename, date_time=ZIP_DATE)
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o600 << 16
            target.writestr(entry, source.read(info.filename))
    return output.getvalue()
