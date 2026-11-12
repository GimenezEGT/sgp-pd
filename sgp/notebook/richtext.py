"""Texto formatado do caderno: lista branca aplicada no servidor (contrato conteudo-assinado.md).

O editor (static/notebook/editor.js) manda HTML; aqui só passa o que a lista branca aceita. Texto
sem nenhuma tag é tratado como texto simples, como o texto formatado da feature 004.
"""

import re
import unicodedata
from html import escape, unescape

import nh3

TAGS = frozenset(
    {
        "p",
        "br",
        "strong",
        "b",
        "em",
        "i",
        "u",
        "s",
        "sub",
        "sup",
        "ul",
        "ol",
        "li",
        "h3",
        "h4",
        "blockquote",
        "pre",
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
        "img",
    }
)
ATTRIBUTES = {
    "img": {"src", "alt"},
    "td": {"colspan", "rowspan"},
    "th": {"colspan", "rowspan"},
}
IMAGE_SRC = re.compile(r"^/arquivos/(\d+)/$")
SPAN = re.compile(r"^(?:[1-9]|1\d|20)$")
HAS_TAG = re.compile(r"<\s*/?\s*[a-zA-Z!]")
IMG_WITHOUT_SRC = re.compile(r"<img(?![^>]*\ssrc=)[^>]*>")
ANY_TAG = re.compile(r"<[^>]+>")
SPACES = re.compile(r"\s+")
DIV = re.compile(r"<(/?)div", re.IGNORECASE)


def plain_to_html(text: str) -> str:
    """Parágrafos (linha em branco) e listas simples ("- "), sempre escapados."""
    html = []
    for block in (text or "").replace("\r\n", "\n").split("\n\n"):
        lines = [line for line in block.split("\n") if line.strip()]
        if not lines:
            continue
        if all(line.lstrip().startswith("- ") for line in lines):
            items = "".join(f"<li>{escape(line.lstrip()[2:])}</li>" for line in lines)
            html.append(f"<ul>{items}</ul>")
        else:
            html.append("<p>" + "<br>".join(escape(line) for line in lines) + "</p>")
    return "".join(html)


def sanitize(value: str, *, image_ids=frozenset()) -> str:
    """HTML limpo pela lista branca; imagem só de anexo ativo da entrada (`image_ids`)."""
    text = (value or "").replace("\r\n", "\n").strip()
    if not text:
        return ""
    if not HAS_TAG.search(text):
        text = plain_to_html(text)
    text = DIV.sub(lambda match: "<" + match.group(1) + "p", text)
    allowed = {int(item) for item in image_ids}

    def attribute_filter(tag, attribute, attr_value):
        if tag == "img" and attribute == "src":
            match = IMAGE_SRC.match(attr_value or "")
            return attr_value if match and int(match.group(1)) in allowed else None
        if attribute in ("colspan", "rowspan"):
            return attr_value if SPAN.match(attr_value or "") else None
        return attr_value

    cleaned = nh3.clean(
        text,
        tags=set(TAGS),
        attributes={tag: set(names) for tag, names in ATTRIBUTES.items()},
        attribute_filter=attribute_filter,
        clean_content_tags={"script", "style"},
        strip_comments=True,
        link_rel=None,
        url_schemes=set(),
    )
    cleaned = IMG_WITHOUT_SRC.sub("", cleaned)
    return cleaned.strip()


def image_ids(html: str) -> set[int]:
    """Ids dos arquivos citados nas imagens do texto."""
    found = set()
    for src in re.findall(r'<img[^>]*\ssrc="([^"]+)"', html or ""):
        match = IMAGE_SRC.match(src)
        if match:
            found.add(int(match.group(1)))
    return found


def plain_text(html: str) -> str:
    """Texto puro (para busca e resumo da linha do tempo)."""
    text = ANY_TAG.sub(" ", html or "")
    return SPACES.sub(" ", unescape(text)).strip()


def fold(text: str) -> str:
    """Minúsculas sem acentos: a busca compara "solucao" com "solução"."""
    decomposed = unicodedata.normalize("NFKD", text or "")
    return "".join(char for char in decomposed if not unicodedata.combining(char)).lower()


def excerpt(html: str, size: int = 200) -> str:
    text = plain_text(html)
    return text if len(text) <= size else text[: size - 1].rstrip() + chr(0x2026)
