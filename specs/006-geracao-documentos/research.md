# Research: Geração de documentos no padrão da empresa

## R1. Abordagem de geração (prova de layout)

- **Decision**: PDF oficial em HTML com CSS paginado no WeasyPrint, PDF/A-2b; DOCX de conferência
  montado com python-docx a partir do mesmo modelo de renderização e dos mesmos parâmetros de layout.
- **Rationale**: na prova (pasta `prova-layout/`), as duas abordagens reproduziram a capa da Entrada
  e a tabela de 120 linhas com o cabeçalho repetido, "Página N de M" e o selo; a fidelidade empatou
  (a referência disponível é a planilha; os .docx originais não estão no repositório). Desempatam:
  o WeasyPrint gera o mesmo arquivo para o mesmo conteúdo (FR-017, SC-005), é 3 vezes mais rápido,
  acrescenta cerca de 60 MB à imagem em vez de 800 MB, controla a marca d'água e deixa o modelo de
  layout como parâmetros que a Qualidade edita num formulário e que a feature 013 compara item a item.
  O PDF/A-2b passou no veraPDF 1.30.3 antes e depois do selo, desde que imagens não peçam
  interpolação (regra 6.2.8-3), o que o CSS garante.
- **Alternatives considered**: (a) docxtpl + LibreOffice headless: DOCX nativo e PDF/A válido, mas
  sem determinismo (data e identificador mudam a cada conversão), lento, pesado e com marca d'água
  só por opção de exportação; o modelo .docx exigiria que a Qualidade preservasse marcações Jinja.
  Gerar o PDF a partir do DOCX convertido também foi descartado pelos mesmos motivos.

## R2. Fonte

- **Decision**: CSS `font-family: Calibri, Carlito, "DejaVu Sans"`; a imagem instala
  `fonts-crosextra-carlito` (métricas idênticas às da Calibri, licença OFL) e `fonts-dejavu-core`
  como reserva de glifos; o DOCX declara Calibri, que o Word da estação tem.
- **Rationale**: a Calibri não pode ser instalada no servidor sem licença; a Carlito mantém as
  quebras de linha e cobre ≥, ≤, ±, −, °, µ, sobrescritos e gregos. As caixas ☐/☒ dos setores da
  Saída e do formulário opcional são desenhadas por CSS (nenhuma fonte instalada as tem, e glifo
  ausente reprova o PDF/A).
- **Alternatives considered**: Liberation Sans ou DejaVu como fonte principal (métricas diferentes,
  capa diverge da planilha).

## R3. Selo digital

- **Decision**: pyHanko, assinatura PAdES B-B invisível (campo `SeloSGP`), com o certificado da
  empresa em PKCS#12 fora do repositório: `DOCUMENT_SEAL_PKCS12` (caminho) e
  `DOCUMENT_SEAL_PASSWORD` (senha) só em variáveis de ambiente. Sem certificado legível e válido na
  data, a geração do PDF oficial falha (FR-013). Em desenvolvimento, o comando `selo_teste` gera um
  certificado autoassinado em `var/certs/` (ignorado pelo Git) e recusa rodar com `DEBUG` desligado;
  os testes geram um certificado temporário.
- **Rationale**: o selo é verificável em qualquer leitor de PDF (o `pdfsig` e o pyHanko validaram e
  acusaram a alteração de 1 byte); B-B dispensa carimbo do tempo, que não existe na intranet.
- **Alternatives considered**: PAdES B-T/B-LT (exige TSA e informação de revogação; avaliar com o
  certificado ICP-Brasil, fora do escopo); assinatura visível (sem ganho, e o bloco de assinaturas
  já mostra as assinaturas eletrônicas).

## R4. Determinismo e resumos

- **Decision**: o PDF é gerado com identificador fixo derivado do documento e com as datas de
  metadados iguais à data da aprovação (ou do pedido, no rascunho); "resumo do conteúdo" é o SHA-256
  do PDF antes do selo (ou do DOCX normalizado) e "resumo do arquivo" é o SHA-256 do arquivo
  arquivado. O DOCX é normalizado: entradas do ZIP com data fixa e propriedades do documento fixas.
  Cada geração oficial compara o resumo do conteúdo com o da primeira geração da mesma versão e do
  mesmo layout; diferença vira alerta `documents.regeneration_mismatch` (por exemplo, depois de uma
  atualização do gerador, que é mudança sob controle).
- **Rationale**: a prova gerou o mesmo SHA-256 em duas execuções; o selo muda a cada geração (hora
  da assinatura), por isso a comparação é antes do selo.

## R5. Conteúdo congelado na aprovação

- **Decision**: na aprovação (mesma transação da assinatura "aprovado" da feature 005), o sistema
  monta e congela o modelo de renderização da versão (contrato `conteudo-renderizacao.md`):
  rótulos, valores de cadastro resolvidos, nome do produto, numeração, assinaturas e data de
  aprovação, com o modelo de layout da versão, em tabela somente de inclusão (`FrozenRendering`).
  Toda geração de versão aprovada usa só esse conteúdo e o layout congelado. Versões aprovadas antes
  da 006 (só no ambiente de desenvolvimento) são congeladas na primeira geração oficial.
- **Rationale**: renomear o produto (nova versão do TAP) ou o rótulo de uma lista não pode mudar o
  documento aprovado (FR-017, constituição V); o conteúdo canônico da 005 guarda códigos e ids, não
  o que é exibido.
- **Alternatives considered**: renderizar sempre dos dados vivos (quebra FR-017); mudar o conteúdo
  canônico da 005 (invalidaria os resumos já assinados).

## R6. Modelo de layout de cada versão de documento

- **Decision**: tabela somente de inclusão `LayoutBinding` (tipo, documento, versão, modelo de
  layout), gravada quando a versão do documento começa: criação do subdocumento (004), nova versão
  (005) e criação do projeto para TAP e Plano de Negócios (002). Documento sem vínculo (anterior à
  006) é vinculado, na primeira consulta, à primeira versão publicada do layout do alvo.
- **Rationale**: FR-021 e constituição IV: publicar layout novo não muda documento iniciado; a nova
  versão do documento (02, 03…) já nasce no layout vigente.
- **Alternatives considered**: layout vigente na geração (mudaria rascunhos já iniciados);
  calcular pela data de início da versão (a 005 não guarda a data de início das versões seguintes).

## R7. Geração assíncrona

- **Decision**: `GenerationRequest` (situação na fila, gerando, concluída, falhou) criado pela tela;
  tarefa Celery `documents.generate(request_id)` com limite de 120 s; a tela consulta a situação por
  HTMX a cada 2 s até terminar. Pedido igual em andamento (mesmo documento, versão e formato) é
  reaproveitado (FR-002). Nos testes, Celery roda em modo síncrono (`settings_test`).
- **Rationale**: o worker Celery já existe desde a 001; HTMX já é usado sem JavaScript próprio.

## R8. Arquivo dos documentos gerados

- **Decision**: o arquivo vai para o armazenamento por conteúdo da 003 (`StoredFile`, conferido a
  cada leitura), com o novo tipo `docx` (só gerado pelo sistema, nunca aceito em upload); o registro
  `GeneratedDocument` (somente de inclusão) guarda documento, versão, situação, formato, oficial,
  modelos usados, resumos, código e autor. O download passa pela rota da 006, que confere a
  permissão (inclusive a financeira no Plano de Negócios), a integridade e registra o evento.

## R9. Código de verificação

- **Decision**: 16 caracteres em base32 de Crockford (sem I, L, O, U), em grupos de 4, tirados do
  SHA-256 de `tipo:id:versão:resumo do conteúdo congelado:modelo de layout`; calculado antes da
  renderização (o código está no rodapé, então não pode depender do próprio PDF) e igual em toda
  regeneração da mesma versão. A consulta exige login; quem não tem acesso ao projeto vê só a
  validade, o tipo, a versão, a situação, a data de aprovação e o resumo do arquivo (FR-014).

## R10. Modelo de layout

- **Decision**: `LayoutTemplate` por alvo (`subdocument`, `charter`, `business_plan`), com versões
  rascunho/publicada, vigência, `definition` em JSON validada por JSON Schema (contrato
  `modelo-layout.md`) e logotipo opcional (`StoredFile`); sem logotipo enviado, vale a faixa padrão
  "Bioclin · Quibasa" extraída da planilha e guardada como arquivo estático, com o SHA-256 conferido.
  A Qualidade/AR edita por formulário (margens, fontes e tamanhos, recuo da capa, variantes de capa
  por tipo, cabeçalho, rodapé, estilos de tabela e marca d'água), pré-visualiza com dados de exemplo
  e publica; publicado é imutável por serviço e por trigger no banco, como o modelo de formulário da
  004. Variantes de capa por tipo de subdocumento ficam no layout (dado, não código): `topics`
  (padrão), `checklist` (Verificação Final: a tabela CHECK LIST com os dados na capa, sem repetir o
  tópico no corpo) e `sectors` (Saída: setores em duas colunas com caixas marcadas).
- **Rationale**: constituição IV (capas e rodapés configuráveis) e FR-019; o JSON estruturado permite
  a comparação item a item da 013.

## R11. DOCX de conferência

- **Decision**: python-docx monta o DOCX do mesmo modelo de renderização: seção A4 com as margens do
  layout, estilos Calibri, cabeçalho e rodapé com campos PAGE e NUMPAGES, linha de cabeçalho de
  tabela repetida, marca d'água VML no cabeçalho para versões não aprovadas e "Cópia para conferência
  – o documento oficial é o PDF" no rodapé das aprovadas (FR-015).

## R12. Regressão visual e conformidade

- **Decision**: os testes rasterizam páginas com pypdfium2 (dependência de desenvolvimento) e
  comparam com PNGs de referência em `tests/documents/referencias/` com tolerância de diferença;
  as referências são geradas por `scripts/atualizar_referencias_visuais.sh` e só mudam com aprovação
  da Qualidade (pendência a ratificar). A conformidade PDF/A é checada nos testes por marcadores
  estruturais (XMP `pdfaid` parte 2 conformidade B, OutputIntent, fontes embutidas, nenhuma imagem
  com interpolação) e, na validação, pelo veraPDF em contêiner (quickstart).

## R13. TAP e Plano de Negócios

- **Decision**: mesmos geradores com o modelo de renderização montado dos campos da 002 (rótulos dos
  campos como seções numeradas; riscos, partes interessadas, equipe, marcos e previsões como
  tabelas numeradas) e o layout do alvo; rodapé com o texto do layout (vazio por padrão). O Plano de
  Negócios exige permissão de dados financeiros para gerar, baixar e ver o projeto na consulta do
  código (FR-025).

## R14. Calibragem da capa

- **Decision**: o CSS da capa usa as medidas da planilha (prova de layout): faixa de 12,84 × 1,80 cm,
  recuo de 2,44 cm além da margem, segunda coluna de tópicos a 5,09 cm da primeira, passo de 0,77 cm,
  rótulos de assinatura com a linha abaixo; os valores ficam no modelo de layout com esses padrões.
  Abas que a planilha imprime com escala (Saída a 79%) não cabem numa página com os tamanhos
  nominais; o layout guarda o tamanho dos tópicos por tipo, e a Saída usa 11 pt, o tamanho impresso.
  O rodapé do formulário sai no rodapé de todas as páginas (à esquerda) com "Página N de M" à
  direita, para que folhas soltas fiquem identificadas.

## R15. Dependências e imagem

- **Decision**: `weasyprint`, `pyhanko`, `python-docx` no runtime; `pypdfium2` e `pypdf` só nos
  testes. Na imagem: `libpango-1.0-0`, `libpangoft2-1.0-0`, `libharfbuzz-subset0`, `fontconfig`,
  `fonts-crosextra-carlito`, `fonts-dejavu-core`. Nada de LibreOffice.
- **Rationale**: constituição IX (poucas dependências): é o menor conjunto que entrega PDF/A, selo e
  DOCX.
