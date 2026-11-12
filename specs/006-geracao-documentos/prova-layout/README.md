# Prova de layout da feature 006

Executada em 2026-11-08, antes do plano, como pede o `/speckit-plan` da feature: capa da Entrada de
Projeto e tabela de 120 linhas com quebra de página nas duas abordagens, (a) modelo Word com
docxtpl e conversão para PDF/A-2b pelo LibreOffice headless e (b) HTML com CSS paginado no
WeasyPrint, mais o selo PAdES com pyHanko. Os dados são fictícios (`dados.py`); a planilha
`docs/modelos/Capas Projeto.xlsx` só é renderizada como referência visual e de posições.

## Como repetir

```bash
docker build -t sgp-prova-layout:006 specs/006-geracao-documentos/prova-layout
docker run --rm -v "$PWD/var/prova-layout:/work" \
  -v "$PWD/specs/006-geracao-documentos/prova-layout:/prova:ro" \
  -v "$PWD/docs/modelos:/modelos:ro" -v "$PWD/sgp/documents/static/documents:/logo:ro" \
  sgp-prova-layout:006 sh -c 'cp /prova/*.py /work/ && sh /prova/run.sh'
docker run --rm -v "$PWD/var/prova-layout:/data" verapdf/cli:latest --format text /data/out/html.pdf /data/out/html-selado.pdf /data/out/docx.pdf
```

## Resultados (imagem Debian bookworm, WeasyPrint 70.0, LibreOffice 7.4, pyHanko 0.38.1, veraPDF 1.30.3)

| Critério | (a) docxtpl + LibreOffice | (b) HTML + WeasyPrint |
| --- | --- | --- |
| Capa da Entrada (elementos, ordem, fontes e tamanhos) | reproduz | reproduz; posições em cm calibradas pela planilha |
| Tabela de 120 linhas com cabeçalho repetido | sim (linha de cabeçalho marcada) | sim (`thead`) |
| "Página N de M" | sim (campos PAGE e NUMPAGES) | sim (`counter(pages)`) |
| PDF/A-2b no veraPDF | passa | passa depois de desligar a interpolação da imagem (falhava a regra 6.2.8-3) |
| PDF/A-2b depois do selo PAdES | passa | passa |
| Selo validado (pyHanko e `pdfsig`) e adulteração de 1 byte acusada | sim | sim |
| Duas gerações do mesmo conteúdo | arquivos diferentes (data e identificador mudam) | arquivos idênticos (mesmo SHA-256) |
| Tempo de 4 páginas | 1,1 a 1,2 s (conversão) | 0,36 a 0,38 s |
| Acréscimo na imagem Docker | cerca de 800 MB (LibreOffice) | cerca de 60 MB (Pango e fontes) |
| Marca d'água de rascunho | só no PDF, pela opção de exportação (texto verde vertical, sem controle) | CSS: diagonal, cinza, texto e tamanho do modelo de layout |
| Manutenção pela Qualidade | edita o .docx no Word, mas precisa preservar as marcações do modelo; comparação entre versões só por arquivo | parâmetros em formulário, sem marcações; comparação item a item (feature 013) |

Posições medidas na capa da Entrada da planilha (A4, escala 100%, margens 1,3 cm e 2,0 cm): faixa do
logotipo de 12,84 × 1,80 cm; título em 24 pt; produto e versão em 20 pt; "ESTE RELATÓRIO DEVE
CONTER:" em 16 pt a 3,74 cm da borda; tópicos em 14 pt com a segunda coluna a 8,83 cm da borda e
passo de 0,77 cm; bloco de assinaturas em 12 pt com a linha abaixo do rótulo; rodapé do formulário
em 11 pt. A Carlito (métricas idênticas às da Calibri) cobre ≥, ≤, ±, −, °, µ, sobrescritos, letras
gregas e setas, mas não as caixas ☐ e ☒, que são desenhadas por CSS.

Decisão registrada em `research.md` (R1).
