#!/bin/sh
# Prova de layout da feature 006: referência (planilha), abordagens (a) e (b), selo e determinismo.
set -e
cd /work
rm -rf ref out img lo && mkdir -p ref out img
echo "== referência: planilha Capas Projeto renderizada pelo LibreOffice"
cp "/modelos/Capas Projeto.xlsx" ref/capas.xlsx && soffice --headless --convert-to pdf --outdir ref ref/capas.xlsx >/dev/null 2>&1
pdfinfo ref/capas.pdf | grep -E "Pages|Page size"
pdftoppm -r 60 -png ref/capas.pdf img/ref

echo "== (b) HTML + WeasyPrint"
python prova_html.py out/html.pdf
python prova_html.py out/html-2.pdf
python prova_html.py out/html-rascunho.pdf rascunho

echo "== (a) docxtpl + LibreOffice"
python prova_docx.py out/docx.pdf
python prova_docx.py out/docx-2.pdf
python prova_docx.py out/docx-rascunho.pdf rascunho

echo "== páginas e fontes"
for f in out/html.pdf out/docx.pdf; do
  echo "$f: $(pdfinfo $f | grep -E '^Pages|PDF version' | tr -s ' ' | tr '\n' ' ')"
  pdffonts "$f" | tail -n +3
done
echo "== determinismo (sha256 de duas gerações)"
sha256sum out/html.pdf out/html-2.pdf out/docx.pdf out/docx-2.pdf | cut -c1-16,65-

echo "== selo PAdES (pyHanko) e adulteração"
python selo.py out/html.pdf out/docx.pdf
echo "== pdfsig (poppler)"
pdfsig out/html-selado.pdf 2>&1 | grep -E "Signature #|Signer Certificate Common Name|Signature Validation|Certificate Validation|Signature Type" || true
pdfsig out/html-selado-adulterado.pdf 2>&1 | grep -E "Signature Validation" || true

echo "== imagens"
pdftoppm -r 60 -png out/html.pdf img/html
pdftoppm -r 60 -png out/docx.pdf img/docx
pdftoppm -r 60 -png -f 1 -l 2 out/html-rascunho.pdf img/html-rascunho
pdftoppm -r 60 -png -f 1 -l 2 out/docx-rascunho.pdf img/docx-rascunho
ls img | head -50
