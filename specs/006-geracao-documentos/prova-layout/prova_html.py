"""Abordagem (b): HTML com CSS paginado no WeasyPrint, PDF/A-2b."""

import base64
import hashlib
import html
import sys
import time

from weasyprint import HTML

import dados

DASH = chr(0x2013)


def build(rascunho: bool) -> str:
    logo = base64.b64encode(open("/logo/logo-bioclin-quibasa.png", "rb").read()).decode()
    col1, col2 = dados.colunas_capa()

    def lista(col):
        return "".join(f"<li>{n} - {html.escape(t)}</li>" for n, t in col)

    corpo_linhas = "".join(
        "<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in row) + "</tr>"
        for row in dados.linhas()
    )
    cabecalho = "".join(f"<th>{html.escape(c)}</th>" for c in dados.COLUNAS)
    marca = f'<div class="marca">RASCUNHO {DASH} NÃO VÁLIDO</div>' if rascunho else ""
    rodape = f"Formulário Versão: {dados.FORM_VERSAO}. Referência: {dados.REFERENCIA}"
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<title>{dados.TITULO}</title>
<meta name="dcterms.created" content="2026-11-08T10:00:00-03:00">
<meta name="dcterms.modified" content="2026-11-08T10:00:00-03:00">
<style>
@page {{
  size: A4; margin: 2cm 1.3cm 2cm 1.3cm;
  @bottom-left {{ content: "{rodape}"; font: 11pt Calibri, Carlito; vertical-align: top; }}
  @bottom-right {{ content: "Página " counter(page) " de " counter(pages); font: 11pt Calibri, Carlito; vertical-align: top; }}
}}
html {{ font-family: Calibri, Carlito, sans-serif; font-size: 11pt; }}
.capa {{ break-after: page; }}
.logo {{ display: block; width: 12.84cm; height: 1.8cm; margin: 0.4cm auto 2.2cm; image-rendering: crisp-edges; }}
.titulo {{ font-size: 24pt; font-weight: bold; text-align: center; margin: 0 0 .6cm; }}
.produto {{ font-size: 20pt; font-weight: bold; text-transform: uppercase; text-align: center; margin: 0 0 .4cm; }}
.versao {{ font-size: 20pt; text-align: center; margin: 0 0 1.2cm; }}
.conter {{ font-size: 16pt; font-weight: bold; margin: 0 0 .4cm; }}
.colunas {{ display: flex; gap: 1cm; font-size: 14pt; margin-bottom: 1.5cm; }}
.colunas ol {{ list-style: none; margin: 0; padding: 0; flex: 1; }}
.colunas li {{ margin-bottom: .25cm; }}
.assin {{ font-size: 12pt; margin: 0 0 .6cm; }}
.assin b {{ font-weight: bold; }}
h2 {{ font-size: 12pt; font-weight: bold; margin: .4cm 0 .2cm; }}
.tabtitulo {{ font-weight: bold; margin: .3cm 0 .1cm; }}
table {{ border-collapse: collapse; width: 100%; font-size: 10pt; }}
thead {{ display: table-header-group; }}
th {{ background: #d9d9d9; }}
th, td {{ border: .5pt solid #000; padding: 1.5pt 4pt; }}
tr {{ break-inside: avoid; }}
.marca {{ position: fixed; top: 11cm; left: -1cm; width: 21cm; text-align: center;
  transform: rotate(-45deg); white-space: nowrap; font-size: 54pt; font-weight: bold; color: #d0d0d0; z-index: -1; }}
</style></head><body>
{marca}
<section class="capa">
<img class="logo" src="data:image/png;base64,{logo}" alt="Bioclin · Quibasa">
<p class="titulo">{dados.TITULO}</p>
<p class="produto">{dados.PRODUTO}</p>
<p class="versao">VERSÃO {dados.VERSAO}</p>
<p class="conter">ESTE RELATÓRIO DEVE CONTER:</p>
<div class="colunas"><ol>{lista(col1)}</ol><ol>{lista(col2)}</ol></div>
<p class="assin"><b>Analista Responsável (Nome/Função):</b> ________________________________</p>
<p class="assin"><b>Gestor de P&amp;D:</b> ________________________________</p>
<p class="assin"><b>Data: ____</b></p>
</section>
<h2>1. Amostras</h2>
<p>Texto de exemplo do tópico, gerado a partir de dados fictícios.</p>
<p class="tabtitulo">Tabela 01 {DASH} Itens de teste fictícios</p>
<table><thead><tr>{cabecalho}</tr></thead><tbody>{corpo_linhas}</tbody></table>
</body></html>"""


def main():
    out = sys.argv[1]
    rascunho = len(sys.argv) > 2 and sys.argv[2] == "rascunho"
    t0 = time.perf_counter()
    pdf = HTML(string=build(rascunho), base_url=".").write_pdf(
        pdf_variant="pdf/a-2b", pdf_identifier=b"prova-layout-006", uncompressed_pdf=False
    )
    t1 = time.perf_counter()
    open(out, "wb").write(pdf)
    print(f"html {out}: {len(pdf)} bytes, {t1 - t0:.2f}s, sha256={hashlib.sha256(pdf).hexdigest()[:16]}")


if __name__ == "__main__":
    main()
