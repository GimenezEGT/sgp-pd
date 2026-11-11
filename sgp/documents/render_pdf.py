"""PDF/A-2b em HTML com CSS paginado (WeasyPrint), a partir do conteúdo e do layout (research R1).

Determinístico: identificador e datas fixos geram o mesmo arquivo para o mesmo conteúdo (R4).
Só imagens em data URI são aceitas; imagens sem interpolação (veraPDF, regra 6.2.8-3).
"""

import base64
import hashlib

from django.template.loader import render_to_string
from weasyprint import HTML
from weasyprint.urls import URLFetcher

from . import layouts
from .layout_schema import fill

PNG_SIGNATURE = bytes([0x89, 0x50, 0x4E, 0x47])
DASH = chr(0x2013)
BLANK_LINE = "_" * 53
BLANK_DATE = "_" * 13
PAGE_HEIGHT_CM = 29.7
FONT_STACK = '"{family}", "Carlito", "DejaVu Sans", sans-serif'


def css_string(text: str) -> str:
    """Texto como string CSS (aspas, barras e quebras escapadas; sem fechar o <style>)."""
    out = []
    for char in text or "":
        if char in '"\\':
            out.append("\\" + char)
        elif char == "\n":
            out.append("\\A ")
        elif char in "<>":
            out.append(f"\\{ord(char):X} ")
        else:
            out.append(char)
    return '"' + "".join(out) + '"'


def placeholders_for(content: dict) -> dict:
    return {
        "titulo": content["title"],
        "produto": content["product"],
        "versao": content["version"],
        "projeto": content.get("project_code", ""),
    }


def footer_lines(content: dict, definition: dict, *, verification_code: str = "", extra="") -> list:
    values = placeholders_for(content)
    lines = []
    if content.get("form_footer"):
        lines.append(content["form_footer"])
    layout_text = fill(definition["footer"]["text"], values).strip()
    if layout_text:
        lines.append(layout_text)
    if verification_code:
        lines.append(f"Código de verificação: {verification_code}")
    if extra:
        lines.append(extra)
    return lines


def signature_line(signature: dict | None) -> str:
    if not signature:
        return ""
    text = f"{signature['name']}"
    if signature.get("title"):
        text += f" / {signature['title']}"
    text += f" {DASH} assinatura eletrônica ({signature['meaning']}) em {signature['at']}"
    if signature.get("delegation"):
        text += f" {DASH} {signature['delegation']}"
    return text


def cover_signatures(content: dict) -> tuple[dict | None, dict | None]:
    """Bloco da capa: a "Elaborado" mais recente e a "Aprovado" da versão (FR-012)."""
    author = approver = None
    for signature in content.get("signatures", []):
        if signature["meaning_code"] == "elaborated":
            author = signature
        elif signature["meaning_code"] == "approved":
            approver = signature
    return author, approver


def cover_columns(content: dict) -> list[list]:
    topics = content["cover"]["topics"]
    if content["cover"].get("columns", 1) == 2 and topics:
        half = len(topics) // 2
        return [topics[:half], topics[half:]]
    return [topics]


def build_css(content: dict, definition: dict, *, draft: bool, verification_code: str) -> str:
    page, font, cover, body = (
        definition["page"],
        definition["font"],
        definition["cover"],
        definition["body"],
    )
    header = definition["header"]
    watermark = definition["watermark"]
    family = FONT_STACK.format(family=font["family"])
    title_pt = cover.get("title_pt_by_type", {}).get(content.get("type"), cover["title_pt"])
    topics_pt = cover.get("topics_pt_by_type", {}).get(content.get("type"), cover["topics_pt"])
    header_text = fill(header["text"], placeholders_for(content))
    footer = "\n".join(footer_lines(content, definition, verification_code=verification_code))
    content_height = PAGE_HEIGHT_CM - page["margin_top_cm"] - page["margin_bottom_cm"]
    indent = cover["indent_cm"]
    return f"""
@page {{
  size: A4 portrait;
  margin: {page["margin_top_cm"]}cm {page["margin_right_cm"]}cm {page["margin_bottom_cm"]}cm {page["margin_left_cm"]}cm;
  @top-center {{ content: {css_string(header_text)}; font-family: {family}; font-size: {header["pt"]}pt; vertical-align: bottom; padding-bottom: 0.3cm; }}
  @bottom-left {{ content: {css_string(footer)}; white-space: pre-wrap; font-family: {family}; font-size: {definition["footer"]["pt"]}pt; vertical-align: top; padding-top: 0.3cm; }}
  @bottom-right {{ content: "Página " counter(page) " de " counter(pages); font-family: {family}; font-size: {definition["footer"]["pt"]}pt; vertical-align: top; padding-top: 0.3cm; white-space: nowrap; }}
}}
@page :first {{ @top-center {{ content: none; }} }}
html {{ font-family: {family}; font-size: {font["body_pt"]}pt; line-height: 1.25; color: #000; }}
body {{ margin: 0; }}
p {{ margin: 0 0 0.18cm; }}
ul {{ margin: 0 0 0.18cm 0.6cm; padding: 0; }}
li {{ margin: 0 0 0.05cm; }}
.capa {{ break-after: page; }}
.logo {{ display: block; width: {definition["logo"]["width_cm"]}cm; height: {definition["logo"]["height_cm"]}cm; margin: 0.6cm auto 1.95cm; image-rendering: crisp-edges; }}
.titulo {{ font-size: {title_pt}pt; font-weight: bold; text-align: center; margin-bottom: 0.45cm; }}
.produto {{ font-size: {cover["product_pt"]}pt; font-weight: bold; text-align: center; margin-bottom: 0.45cm; }}
.versao {{ font-size: {cover["version_pt"]}pt; text-align: center; margin-bottom: 1.05cm; }}
.versao .num {{ margin-left: 0.6cm; }}
.versao .sep {{ display: inline-block; width: 1cm; }}
.recuo {{ margin-left: {indent}cm; }}
.conter {{ font-size: {cover["contains_pt"]}pt; font-weight: bold; margin-bottom: 0.75cm; }}
table.colunas {{ border-collapse: collapse; font-size: {topics_pt}pt; }}
table.colunas td {{ vertical-align: top; padding: 0; }}
table.colunas td.col1 {{ width: {cover["second_column_cm"]}cm; }}
table.colunas p {{ margin: 0 0 0.15cm; }}
.setores {{ margin-top: 0.35cm; font-size: {topics_pt}pt; }}
.setores td.col1 {{ width: 7cm; }}
.caixa {{ display: inline-block; width: 0.32cm; height: 0.32cm; border: 0.75pt solid #000; margin-right: 0.25cm; vertical-align: -0.04cm; text-align: center; font-size: 8pt; line-height: 0.32cm; font-weight: bold; }}
.assinaturas {{ margin-top: 1.2cm; font-size: {cover["signature_pt"]}pt; break-inside: avoid; }}
.assinaturas .rotulo {{ font-weight: bold; margin-bottom: 0.05cm; }}
.assinaturas .linha {{ margin-bottom: 0.45cm; }}
table.checklist {{ border-collapse: collapse; width: 100%; font-size: {body["table_pt"]}pt; margin-bottom: 0.5cm; }}
table.checklist th {{ font-size: {cover["checklist_header_pt"]}pt; font-weight: bold; text-align: center; border: 0.5pt solid #000; padding: 1.5pt 3pt; }}
table.checklist td {{ border: 0.5pt solid #000; padding: 1.5pt 3pt; vertical-align: top; }}
h2 {{ font-size: {body["heading_pt"]}pt; font-weight: bold; margin: 0.45cm 0 0.2cm; break-after: avoid; }}
.rotulo {{ font-weight: bold; margin-bottom: 0.08cm; break-after: avoid; }}
.tabela-titulo {{ font-weight: bold; margin: 0.3cm 0 0.1cm; break-after: avoid; }}
table.dados {{ border-collapse: collapse; width: 100%; font-size: {body["table_pt"]}pt; margin-bottom: 0.15cm; }}
table.dados th {{ background: {body["table_header_fill"]}; font-weight: bold; text-align: left; }}
table.dados th, table.dados td {{ border: 0.5pt solid #000; padding: 1.5pt 4pt; vertical-align: top; }}
table.dados tr {{ break-inside: avoid; }}
table.dados tr.total td {{ font-weight: bold; }}
.nota {{ font-size: {body["table_pt"] - 1}pt; }}
.observacao {{ font-style: italic; }}
.resumo {{ font-size: 8pt; word-break: break-all; }}
.formulario-opcional {{ break-before: page; }}
.faixa {{ background: {body["table_header_fill"]}; font-weight: bold; font-size: {body["heading_pt"]}pt; padding: 0.15cm 0.25cm; margin-bottom: 0.3cm; }}
.grupo {{ margin-bottom: 0.25cm; }}
.grupo .opcao {{ display: inline-block; margin-right: 0.6cm; }}
.marca {{ position: fixed; left: 0; right: 0; top: {content_height / 2 - 1:.2f}cm; text-align: center; white-space: nowrap;
  transform: rotate(-45deg); font-family: {family}; font-size: {watermark["pt"]}pt; font-weight: bold; color: {watermark["color"]}; z-index: -1; }}
"""


def identifier_for(*parts) -> bytes:
    return hashlib.sha256(":".join(str(part) for part in parts).encode()).hexdigest()[:32].encode()


def render(
    content: dict,
    layout,
    *,
    draft: bool,
    created: str,
    identifier: bytes,
    verification_code: str = "",
) -> bytes:
    definition = layout.definition
    logo = layouts.logo_bytes(layout)
    mime = "image/png" if logo.startswith(PNG_SIGNATURE) else "image/jpeg"
    author, approver = cover_signatures(content)
    html = render_to_string(
        "documents/pdf/document.html",
        {
            "c": content,
            "css": build_css(content, definition, draft=draft, verification_code=verification_code),
            "logo_uri": f"data:{mime};base64,{base64.b64encode(logo).decode()}",
            "watermark": definition["watermark"]["text"] if draft else "",
            "cover_columns": cover_columns(content),
            "author": signature_line(author),
            "approver": signature_line(approver),
            "blank_line": BLANK_LINE,
            "blank_date": BLANK_DATE,
            "created": created,
            "meta_title": f"{content['title']} {DASH} {content['product']} {DASH} Versão {content['version']}",
        },
    )
    fetcher = URLFetcher(allowed_protocols=["data"])
    return HTML(string=html, url_fetcher=fetcher).write_pdf(
        pdf_variant="pdf/a-2b", pdf_identifier=identifier
    )
