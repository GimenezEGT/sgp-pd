"""HTML único do documento completo, renderizado pelo WeasyPrint (research R1).

O sumário usa target-counter: o número de cada parte é o da página real em que ela começa. Os
estilos de capa e tópicos são os do layout vigente da 006; as regras de página são próprias
(cabeçalho com o título da parte, rodapé do documento completo e "Página X de Y" global).
"""

import base64

from django.template.loader import render_to_string
from weasyprint import HTML
from weasyprint.urls import URLFetcher

from sgp.documents import layouts, render_pdf
from sgp.documents.layout_schema import fill

FORMAT_TITLE = "Documento completo do projeto"


def base_content(project) -> dict:
    """Conteúdo mínimo para os textos de cabeçalho e rodapé do documento completo."""
    return {
        "title": FORMAT_TITLE,
        "product": (project.product_name or "").upper(),
        "version": f"{project.version or 0:02d}",
        "project_code": project.code or "",
        "type": "",
        "form_footer": "",
    }


def _page_rules(definition: dict, *, footer: str) -> str:
    page, font, header = definition["page"], definition["font"], definition["header"]
    family = render_pdf.FONT_STACK.format(family=font["family"])
    footer_pt = definition["footer"]["pt"]
    return f"""
@page {{
  size: A4 portrait;
  margin: {page["margin_top_cm"]}cm {page["margin_right_cm"]}cm {page["margin_bottom_cm"]}cm {page["margin_left_cm"]}cm;
  @top-center {{ content: string(cabecalho); font-family: {family}; font-size: {header["pt"]}pt; vertical-align: bottom; padding-bottom: 0.3cm; }}
  @bottom-left {{ content: {render_pdf.css_string(footer)}; white-space: pre-wrap; font-family: {family}; font-size: {footer_pt}pt; vertical-align: top; padding-top: 0.3cm; }}
  @bottom-right {{ content: "Página " counter(page) " de " counter(pages); font-family: {family}; font-size: {footer_pt}pt; vertical-align: top; padding-top: 0.3cm; white-space: nowrap; }}
}}
@page capa {{ @top-center {{ content: none; }} }}
"""


def _type_rules(definition: dict, types: set[str]) -> str:
    cover = definition["cover"]
    rules = []
    for code in sorted(types):
        title_pt = cover.get("title_pt_by_type", {}).get(code, cover["title_pt"])
        topics_pt = cover.get("topics_pt_by_type", {}).get(code, cover["topics_pt"])
        rules.append(
            f".parte-{code} .titulo {{ font-size: {title_pt}pt; }}\n"
            f".parte-{code} table.colunas, .parte-{code} .setores {{ font-size: {topics_pt}pt; }}"
        )
    return "\n".join(rules)


EXTRA_CSS = """
.capa, .capa-geral, .substituida { page: capa; }
.capa-geral { break-after: page; }
.capa-geral .dados { margin-top: 1.5cm; }
.parte { break-before: page; bookmark-level: 1; bookmark-label: attr(data-titulo); string-set: cabecalho attr(data-cabecalho); }
h1.parte-titulo { font-size: 14pt; font-weight: bold; margin: 0 0 0.4cm; bookmark-level: none; }
.sumario { break-after: page; string-set: cabecalho "Sumário"; }
.sumario h1 { font-size: 14pt; margin: 0 0 0.5cm; bookmark-level: none; }
.sumario ol { list-style: none; margin: 0; padding: 0; }
.sumario li { margin: 0 0 0.12cm; }
.sumario a { color: #000; text-decoration: none; }
.sumario a::after { content: leader(".") target-counter(attr(href), page); }
.substituida { border: 1pt solid #000; padding: 0.1cm 0.25cm; font-weight: bold; margin-bottom: 0.3cm; }
.entrada-caderno { break-inside: avoid-page; margin-bottom: 0.5cm; }
.texto-caderno table { border-collapse: collapse; margin: 0.15cm 0; }
.texto-caderno th, .texto-caderno td { border: 0.5pt solid #000; padding: 1.5pt 4pt; }
.texto-caderno img { max-width: 100%; height: auto; }
"""


def build_css(
    project, composition: dict, definition: dict, *, draft: bool, verification_code: str
) -> str:
    content = base_content(project)
    base = render_pdf.build_css(content, definition, draft=draft, verification_code="")
    body_rules = base[base.index("\nhtml {") :]
    footer = "\n".join(
        render_pdf.footer_lines(content, definition, verification_code=verification_code)
    )
    types = {
        part["content"].get("type") or ""
        for part in composition["parts"]
        if part["kind"] == "document"
    }
    return (
        _page_rules(definition, footer=footer)
        + body_rules
        + _type_rules(definition, {t for t in types if t})
        + EXTRA_CSS
    )


def _decorate(parts: list[dict], definition: dict) -> list[dict]:
    """Dados de exibição de cada parte (fora do resumo da composição)."""
    header = definition["header"]["text"]
    shown = []
    for part in parts:
        item = dict(part)
        if part["kind"] == "document":
            content = part["content"]
            author, approver = render_pdf.cover_signatures(content)
            item["cover_columns"] = render_pdf.cover_columns(content)
            item["author"] = render_pdf.signature_line(author)
            item["approver"] = render_pdf.signature_line(approver)
            item["header"] = fill(header, render_pdf.placeholders_for(content))
            item["type"] = content.get("type") or ""
        else:
            item["header"] = part["toc"]
        shown.append(item)
    return shown


def render(
    project,
    composition: dict,
    layout,
    *,
    draft: bool,
    created: str,
    generated_label: str,
    identifier: bytes,
    verification_code: str = "",
) -> tuple[bytes, int]:
    definition = layout.definition
    logo = layouts.logo_bytes(layout)
    mime = "image/png" if logo.startswith(render_pdf.PNG_SIGNATURE) else "image/jpeg"
    html = render_to_string(
        "fulldoc/pdf/document.html",
        {
            "project": project,
            "parts": _decorate(composition["parts"], definition),
            "options": composition["options"],
            "with_financials": composition["with_financials"],
            "css": build_css(
                project,
                composition,
                definition,
                draft=draft,
                verification_code=verification_code,
            ),
            "logo_uri": f"data:{mime};base64,{base64.b64encode(logo).decode()}",
            "watermark": definition["watermark"]["text"] if draft else "",
            "official": not draft,
            "blank_line": render_pdf.BLANK_LINE,
            "blank_date": render_pdf.BLANK_DATE,
            "created": created,
            "generated_label": generated_label,
            "version": f"{project.version or 0:02d}",
            "meta_title": f"{FORMAT_TITLE} {render_pdf.DASH} {project.code or project.title}",
        },
    )
    fetcher = URLFetcher(allowed_protocols=["data"])
    document = HTML(string=html, url_fetcher=fetcher).render(
        pdf_variant="pdf/a-2b", pdf_identifier=identifier
    )
    data = document.write_pdf(pdf_variant="pdf/a-2b", pdf_identifier=identifier)
    return data, len(document.pages)
