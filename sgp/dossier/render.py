"""Dossiê em PDF/A (WeasyPrint) e DOCX (python-docx) no formato do contexto (research R4).

Cabeçalho "Dossiê Técnico <produto>" e rodapé com a razão social e a página, em itálico; itens em
romanos e caixa alta, subitens em letras, terceiro nível em números; tabelas numeradas; nome do
produto em itálico no texto; não aplicável com a justificativa; declaração do responsável técnico e
legal com o texto do contexto.
"""

import io
import re
from html import escape

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from weasyprint import HTML
from weasyprint.urls import URLFetcher

from sgp.documents.render_pdf import css_string

MONTHS = (
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)
WATERMARK = "RASCUNHO – NÃO VÁLIDO"
FONT = '"Calibri", "Carlito", "DejaVu Sans", sans-serif'


def date_long(day) -> str:
    return f"{day.day} de {MONTHS[day.month - 1]} de {day.year}"


def declaration(company) -> str:
    """Texto da declaração do contexto (docs/contexto/03-padroes-formatacao.md)."""
    return (
        f"O abaixo assinado {company.rt_name}, inscrito no {company.rt_council} de {company.rt_uf} "
        f"sob nº {company.rt_number}, assume a responsabilidade pelas informações fornecidas "
        "nesse Dossiê Técnico."
    )


# ------------------------------------------------------------------ árvore comum


def build_tree(parsed: dict, checklist: dict) -> dict:
    """Itens com os blocos, tabelas numeradas e anexos numerados na ordem de leitura."""
    by_key = {item["key"]: item for item in checklist["items"]}
    annexes: dict[int, dict] = {}
    counter = {"table": 0}

    def number_blocks(blocks):
        out = []
        for block in blocks:
            block = dict(block)
            if block.get("kind") == "table" and block.get("rows"):
                counter["table"] += 1
                block["number"] = f"Tabela {counter['table']:02d}"
            out.append(block)
        return out

    def walk(items, level):
        nodes = []
        for item in items:
            node = {
                "key": item["key"],
                "numero": item["numero"],
                "titulo": item["titulo"],
                "level": level,
            }
            if item.get("subitens"):
                node["children"] = walk(item["subitens"], level + 1)
            else:
                entry = by_key[item["key"]]
                node.update(
                    status=entry["status"],
                    justification=entry.get("justification", ""),
                    reason=entry.get("reason", ""),
                    blocks=number_blocks(entry.get("blocks", [])),
                )
                refs = []
                for stored in entry.get("annexes", []):
                    if stored.pk not in annexes:
                        annexes[stored.pk] = {
                            "number": len(annexes) + 1,
                            "file": stored,
                            "origin": f"{item['numero']}. {item['titulo']}",
                        }
                    refs.append(annexes[stored.pk])
                node["annexes"] = refs
            nodes.append(node)
        return nodes

    return {"nodes": walk(parsed["itens"], 1), "annexes": list(annexes.values())}


def _label(node) -> str:
    title = node["titulo"].upper() if node["level"] == 1 else node["titulo"]
    return f"{node['numero']}. {title}"


def _lines(block) -> list[str]:
    kind = block.get("kind")
    if kind == "values":
        return [line for line in block.get("lines", []) if line]
    if kind == "rich":
        out = []
        for item in block.get("items", []):
            out += (
                [f"- {li}" for li in item.get("ul", [])] if item.get("ul") else [item.get("p", "")]
            )
        return out
    if kind == "table":
        rows = [" | ".join(block.get("columns", []))]
        rows += [" | ".join(str(cell) for cell in row) for row in block.get("rows", [])]
        return [block.get("label", "")] + rows
    if kind == "files":
        return [f"{f.get('name')} (SHA-256 {f.get('sha256')})" for f in block.get("files", [])]
    if kind in ("note", "empty"):
        return [block.get("text", "")]
    return []


def canonical(tree: dict) -> dict:
    """Texto por item (para o aditamento e o resumo)."""
    out = {}

    def walk(nodes, path):
        for node in nodes:
            label = f"{path} › {_label(node)}" if path else _label(node)
            if node.get("children"):
                walk(node["children"], label)
                continue
            lines = []
            if node["status"] == "na":
                lines.append(f"Não aplicável. {node['justification']}")
            for block in node["blocks"]:
                if block.get("label") and block.get("kind") != "table":
                    lines.append(f"{block['label']}:")
                lines += _lines(block)
            for ref in node["annexes"]:
                lines.append(
                    f"Anexo {ref['number']:02d} – {ref['file'].original_name} ({ref['file'].sha256})"
                )
            out[node["key"]] = {"titulo": label, "status": node["status"], "linhas": lines}

    walk(tree["nodes"], "")
    return out


# ------------------------------------------------------------------ PDF


def _italic_product(text: str, product: str) -> str:
    html = escape(text or "")
    if product:
        html = re.sub(
            re.escape(escape(product)),
            lambda m: f"<em>{m.group(0)}</em>",
            html,
            flags=re.IGNORECASE,
        )
    return html


def _html_block(block: dict, product: str) -> str:
    kind = block.get("kind")
    label = block.get("label") or ""
    if kind == "table":
        if not block.get("rows"):
            return ""
        head = "".join(f"<th>{escape(str(c))}</th>" for c in block.get("columns", []))
        body = "".join(
            "<tr>"
            + "".join(f"<td>{_italic_product(str(cell), product)}</td>" for cell in row)
            + "</tr>"
            for row in block.get("rows", [])
        )
        title = f'<p class="tabela-titulo">{escape(block.get("number", ""))} – {escape(label)}</p>'
        return f'{title}<table class="dados"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'
    lines = _lines(block)
    if not lines:
        return ""
    prefix = f'<p class="rotulo">{escape(label)}:</p>' if label else ""
    if kind == "rich":
        parts = []
        for item in block.get("items", []):
            if item.get("ul"):
                parts.append(
                    "<ul>"
                    + "".join(f"<li>{_italic_product(li, product)}</li>" for li in item["ul"])
                    + "</ul>"
                )
            else:
                parts.append(
                    "<p>"
                    + "<br>".join(
                        _italic_product(line, product) for line in item.get("p", "").split("\n")
                    )
                    + "</p>"
                )
        return prefix + "".join(parts)
    if kind in ("note", "empty"):
        return f'<p class="nota">{_italic_product(lines[0], product)}</p>'
    if len(lines) == 1:
        return prefix + f"<p>{_italic_product(lines[0], product)}</p>"
    return (
        prefix
        + "<ul>"
        + "".join(f"<li>{_italic_product(line, product)}</li>" for line in lines)
        + "</ul>"
    )


def _html_nodes(nodes, product: str) -> str:
    out = []
    for node in nodes:
        tag = {1: "h1", 2: "h2"}.get(node["level"], "h3")
        out.append(f"<{tag}>{escape(_label(node))}</{tag}>")
        if node.get("children"):
            out.append(_html_nodes(node["children"], product))
            continue
        if node["status"] == "na":
            out.append(f"<p>Não aplicável. {_italic_product(node['justification'], product)}</p>")
        elif node["status"] == "missing":
            out.append(f'<p class="faltando">Faltando: {escape(node["reason"])}</p>')
        for block in node["blocks"]:
            out.append(_html_block(block, product))
        for ref in node["annexes"]:
            out.append(
                f"<p>Ver Anexo {ref['number']:02d} – {escape(ref['file'].original_name)}.</p>"
            )
    return "".join(out)


def pdf(
    *, tree, product: str, company, draft: bool, missing: list, day, identifier: bytes
) -> bytes:
    header = f"Dossiê Técnico {product}"
    legal = company.legal_name if company else "(razão social não cadastrada)"
    css = f"""
@page {{ size: A4; margin: 2.5cm 2cm 2.5cm 2.5cm;
  @top-center {{ content: {css_string(header)}; font-style: italic; font-family: {FONT}; font-size: 9pt; }}
  @bottom-left {{ content: {css_string(legal)}; font-style: italic; font-family: {FONT}; font-size: 9pt; }}
  @bottom-right {{ content: counter(page); font-style: italic; font-family: {FONT}; font-size: 9pt; }} }}
html {{ font-family: {FONT}; font-size: 11pt; line-height: 1.3; }}
h1 {{ font-size: 12pt; font-weight: bold; margin: 0.6cm 0 0.2cm; }}
h2 {{ font-size: 11pt; font-weight: bold; margin: 0.4cm 0 0.15cm; }}
h3 {{ font-size: 11pt; font-weight: bold; margin: 0.3cm 0 0.1cm; }}
.titulo {{ font-size: 16pt; font-weight: bold; text-align: center; margin-top: 1cm; }}
.produto {{ font-size: 14pt; font-style: italic; text-align: center; margin-bottom: 1cm; }}
.rotulo {{ font-weight: bold; margin-bottom: 0.05cm; }}
.tabela-titulo {{ font-weight: bold; margin: 0.25cm 0 0.1cm; }}
table.dados {{ border-collapse: collapse; width: 100%; font-size: 9.5pt; margin-bottom: 0.2cm; }}
table.dados th, table.dados td {{ border: 0.5pt solid #000; padding: 1.5pt 4pt; vertical-align: top; text-align: left; }}
.nota {{ font-style: italic; font-size: 10pt; }}
.faltando {{ color: #a4262c; font-weight: bold; }}
.declaracao {{ margin-top: 1cm; break-inside: avoid; }}
.assinatura {{ margin-top: 1.5cm; }}
.marca {{ position: fixed; top: 11cm; left: 0; right: 0; text-align: center; transform: rotate(-45deg); font-size: 40pt; color: #d9d9d9; font-weight: bold; z-index: -1; }}
.resumo {{ font-size: 8pt; word-break: break-all; }}
"""
    parts = [
        f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>{escape(header)}</title><style>{css}</style></head><body>'
    ]
    if draft:
        parts.append(f'<div class="marca">{escape(WATERMARK)}</div>')
    parts.append(f'<p class="titulo">DOSSIÊ TÉCNICO</p><p class="produto">{escape(product)}</p>')
    if draft and missing:
        parts.append("<h1>Pendências para o dossiê final</h1><ul>")
        parts += [f"<li>{escape(m['path_label'])}: {escape(m['reason'])}</li>" for m in missing]
        parts.append("</ul>")
    parts.append(_html_nodes(tree["nodes"], product))
    if tree["annexes"]:
        parts.append(
            '<h1>ANEXOS</h1><table class="dados"><thead><tr><th>Nº</th><th>Arquivo</th><th>Item</th><th>SHA-256</th></tr></thead><tbody>'
        )
        for ref in tree["annexes"]:
            parts.append(
                f"<tr><td>{ref['number']:02d}</td><td>{escape(ref['file'].original_name)}</td>"
                f'<td>{escape(ref["origin"])}</td><td class="resumo">{ref["file"].sha256}</td></tr>'
            )
        parts.append("</tbody></table>")
    if company:
        parts.append(
            f'<div class="declaracao"><p>{escape(declaration(company))}</p>'
            f"<p>{escape(company.city)}, {escape(date_long(day))}.</p>"
            f'<div class="assinatura"><p>______________________________________</p>'
            f"<p>{escape(company.rt_name)}</p>"
            + (f"<p>{escape(company.rt_title)}</p>" if company.rt_title else "")
            + "<p>Responsável Técnico e Legal</p></div></div>"
        )
    parts.append("</body></html>")
    fetcher = URLFetcher(allowed_protocols=["data"])
    return HTML(string="".join(parts), url_fetcher=fetcher).write_pdf(
        pdf_variant="pdf/a-2b", pdf_identifier=identifier
    )


# ------------------------------------------------------------------ DOCX


def _italic_runs(paragraph, text: str, product: str, *, bold=False, size=None):
    pieces = (
        re.split(f"({re.escape(product)})", text or "", flags=re.IGNORECASE) if product else [text]
    )
    for piece in pieces:
        if not piece:
            continue
        run = paragraph.add_run(piece)
        run.bold = bold
        run.italic = bool(product) and piece.lower() == product.lower()
        if size:
            run.font.size = Pt(size)
    return paragraph


def _page_field(paragraph):
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    run = OxmlElement("w:r")
    text = OxmlElement("w:t")
    text.text = "1"
    run.append(text)
    field.append(run)
    paragraph._p.append(field)


def _heading(document, text: str, level: int):
    paragraph = document.add_heading(level=min(level, 3))
    run = paragraph.add_run(text)
    run.font.color.rgb = RGBColor(0, 0, 0)
    run.font.size = Pt(12 if level == 1 else 11)
    run.bold = True
    return paragraph


def _docx_block(document, block: dict, product: str):
    kind = block.get("kind")
    label = block.get("label") or ""
    if kind == "table":
        if not block.get("rows"):
            return
        title = document.add_paragraph()
        title.add_run(f"{block.get('number', '')} – {label}").bold = True
        columns = block.get("columns", [])
        table = document.add_table(rows=1, cols=len(columns))
        table.style = "Table Grid"
        for index, column in enumerate(columns):
            table.rows[0].cells[index].text = str(column)
        for row in block.get("rows", []):
            cells = table.add_row().cells
            for index, value in enumerate(row[: len(columns)]):
                cells[index].text = str(value)
        return
    lines = _lines(block)
    if not lines:
        return
    if label and kind != "rich":
        document.add_paragraph().add_run(f"{label}:").bold = True
    for line in lines:
        paragraph = document.add_paragraph()
        _italic_runs(paragraph, line, product)
        if kind in ("note", "empty"):
            for run in paragraph.runs:
                run.italic = True


def _docx_nodes(document, nodes, product: str):
    for node in nodes:
        _heading(document, _label(node), node["level"])
        if node.get("children"):
            _docx_nodes(document, node["children"], product)
            continue
        if node["status"] == "na":
            _italic_runs(
                document.add_paragraph(), f"Não aplicável. {node['justification']}", product
            )
        elif node["status"] == "missing":
            run = document.add_paragraph().add_run(f"Faltando: {node['reason']}")
            run.bold = True
        for block in node["blocks"]:
            _docx_block(document, block, product)
        for ref in node["annexes"]:
            document.add_paragraph(f"Ver Anexo {ref['number']:02d} – {ref['file'].original_name}.")


def docx(*, tree, product: str, company, draft: bool, missing: list, day) -> bytes:
    document = Document()
    section = document.sections[0]
    section.page_height, section.page_width = Cm(29.7), Cm(21)
    section.top_margin = section.bottom_margin = Cm(2.5)
    section.left_margin, section.right_margin = Cm(2.5), Cm(2)
    style = document.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    header.add_run(f"Dossiê Técnico {product}").italic = True
    footer = section.footer.paragraphs[0]
    footer.add_run(
        (company.legal_name if company else "(razão social não cadastrada)") + "\t\t"
    ).italic = True
    _page_field(footer)
    if draft:
        warning = document.add_paragraph()
        run = warning.add_run(WATERMARK)
        run.bold = True
        run.font.color.rgb = RGBColor(0xA4, 0x26, 0x2C)
    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run("DOSSIÊ TÉCNICO").bold = True
    name = document.add_paragraph()
    name.alignment = WD_ALIGN_PARAGRAPH.CENTER
    name.add_run(product).italic = True
    if draft and missing:
        document.add_paragraph().add_run("Pendências para o dossiê final").bold = True
        for item in missing:
            document.add_paragraph(f"{item['path_label']}: {item['reason']}")
    _docx_nodes(document, tree["nodes"], product)
    if tree["annexes"]:
        _heading(document, "ANEXOS", 1)
        table = document.add_table(rows=1, cols=4)
        table.style = "Table Grid"
        for index, column in enumerate(("Nº", "Arquivo", "Item", "SHA-256")):
            table.rows[0].cells[index].text = column
        for ref in tree["annexes"]:
            cells = table.add_row().cells
            cells[0].text = f"{ref['number']:02d}"
            cells[1].text = ref["file"].original_name
            cells[2].text = ref["origin"]
            cells[3].text = ref["file"].sha256
    if company:
        document.add_paragraph(declaration(company))
        document.add_paragraph(f"{company.city}, {date_long(day)}.")
        document.add_paragraph("______________________________________")
        document.add_paragraph(company.rt_name)
        if company.rt_title:
            document.add_paragraph(company.rt_title)
        document.add_paragraph("Responsável Técnico e Legal")
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def addendum_pdf(*, product: str, version, previous, changes: list, identifier: bytes) -> bytes:
    rows = []
    for change in changes:
        before = "<br>".join(escape(line) for line in change["before"]) or "(sem conteúdo)"
        after = "<br>".join(escape(line) for line in change["after"]) or "(sem conteúdo)"
        rows.append(
            f'<h2>{escape(change["titulo"])}</h2><table class="dados"><thead><tr><th>Versão enviada ({previous.number:02d})</th>'
            f"<th>Versão atual ({version.number:02d})</th></tr></thead><tbody><tr><td>{before}</td><td>{after}</td></tr></tbody></table>"
        )
    css = f"""@page {{ size: A4; margin: 2cm; @top-center {{ content: {css_string("Aditamento – Dossiê Técnico " + product)}; font-style: italic; font-size: 9pt; }}
  @bottom-right {{ content: counter(page); font-size: 9pt; }} }}
html {{ font-family: {FONT}; font-size: 10pt; }} h2 {{ font-size: 11pt; }}
table.dados {{ border-collapse: collapse; width: 100%; }} table.dados th, table.dados td {{ border: 0.5pt solid #000; padding: 2pt 4pt; vertical-align: top; width: 50%; }}"""
    html = (
        f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Aditamento</title><style>{css}</style></head><body>'
        f"<h1>Aditamento ao Dossiê Técnico <em>{escape(product)}</em></h1>"
        f"<p>Itens alterados desde a versão {previous.number:02d}, enviada: {len(changes)}.</p>"
        + "".join(rows)
        + "</body></html>"
    )
    return HTML(string=html, url_fetcher=URLFetcher(allowed_protocols=["data"])).write_pdf(
        pdf_variant="pdf/a-2b", pdf_identifier=identifier
    )
