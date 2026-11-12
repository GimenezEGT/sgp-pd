# Research: Documento completo do projeto

## R1. Composição num único HTML com sumário pela paginação do WeasyPrint

- **Decision**: o documento completo é um único HTML renderizado pelo WeasyPrint (o mesmo motor
  e o mesmo layout da 006): capa geral, sumário, TAP, Plano de Negócios, cada subdocumento com a
  sua capa e os tópicos (o trecho de bloco da 006), quadro de versões, histórico do caderno,
  resumo da trilha e lista de anexos. Cada parte começa em página nova; o cabeçalho corrente mostra
  o título da parte (`string-set`); o rodapé traz "Página X de Y" do documento inteiro; o sumário
  usa `target-counter(attr(href), page)`, que o WeasyPrint resolve na própria paginação, de modo que
  o número no sumário é sempre o da página real (SC-001).
- **Rationale**: uma passagem de layout garante sumário e numeração coerentes; nenhum número é
  calculado à mão.
- **Alternatives considered**: juntar os PDFs prontos de cada subdocumento (pypdf) e carimbar a
  numeração global — perde o sumário com a página real, mistura numerações e exigiria duas passagens
  com carimbo; rejeitado.

## R2. Reaproveitamento por resumo (cache)

- **Decision**: o conteúdo de cada versão aprovada já está congelado na aprovação (`FrozenRendering`
  da 006, com resumo); a geração não remonta nada que já está congelado. O documento completo guarda
  o resumo da composição (projeto, versão do projeto, versões e resumos congelados de cada parte,
  opções, layout, entradas do caderno e último evento da trilha considerado); um novo pedido com o
  mesmo resumo devolve o arquivo já arquivado (evento de reaproveitamento), sem renderizar de novo.
- **Rationale**: atende "reaproveitar quando a versão não mudou" sem quebrar o sumário (R1).

## R3. Geração assíncrona com progresso

- **Decision**: pedido assíncrono pelo Celery, como a 006 (`GenerationRequest` com o tipo
  `project`), com etapas e percentual gravados (montagem, renderização, selo, arquivo); a tela
  atualiza o progresso por HTMX (`hx-trigger="every 2s"`), sem script inline.

## R4. Oficial ou rascunho

- **Decision**: sem pendências, o documento sai oficial (PDF/A-2b, selo da empresa, código de
  verificação, arquivado com SHA-256), como na 006; com pendências, sai como rascunho com marca
  d'água e a lista de pendências logo depois da capa, e não é oficial.

## R5. Desempenho

- **Decision**: teste automatizado com um projeto sintético grande (centenas de páginas) medindo o
  tempo total da geração; meta de 300 páginas em menos de 3 minutos (SC-003) conferida também na
  homologação.

## R6. Partes e conteúdo congelado

- **Decision**: TAP e Plano de Negócios entram pelo conteúdo congelado na aprovação do projeto, e
  cada subdocumento pela versão aprovada vigente (`FrozenRendering`), com a capa e os tópicos da
  006 (o trecho do template é extraído para `_cover.html` e `_sections.html`, usado pelos dois
  geradores). Versão aprovada sem conteúdo congelado (aprovada antes da 006) vira pendência, e não
  é remontada a partir do rascunho atual. No histórico completo, as versões substituídas entram
  depois da vigente, com a faixa "Versão substituída".

## R7. Plano de Negócios sem permissão financeira

- **Decision**: as seções do Plano de Negócios cujos rótulos correspondem aos campos financeiros
  (`FINANCIAL_FIELDS` da 002) e a tabela de retorno esperado são trocadas pela observação "Dado
  financeiro omitido (acesso restrito)" quando quem gera não vê dados financeiros; o documento
  guarda `with_financials` e só quem tem a permissão baixa o que contém esses dados.

## R8. Pendências

- **Decision**: projeto sem TAP e Plano de Negócios aprovados; cada tipo do fluxo do PSG 20
  (Entrada, Formulação, Lote Piloto, RAPD, Análise Crítica, Validação, Verificação Final, Saída)
  sem versão aprovada; subdocumento existente sem versão aprovada (inclusive Alteração de Projeto em
  andamento); versão aprovada sem conteúdo congelado; e cada item da Verificação Final aprovada com
  disposição diferente de "Aprovado" (com a justificativa registrada). A lista aparece na tela antes
  de gerar e, no rascunho, logo depois do sumário.

## R9. Resumo da trilha, quadro de versões, caderno e anexos

- **Decision**: resumo da trilha com período, contagem por tipo de evento (rótulo do catálogo da
  001) e eventos-chave (assinaturas, aprovações, devoluções, novas versões, alterações de projeto e
  documentos oficiais gerados) com data e hora, pessoa e registro, até o momento da geração; quadro
  de versões com cada versão aprovada (documento, versão, data de aprovação, signatários com
  significado); caderno com as entradas assinadas ou testemunhadas, completo (textos sanitizados da
  008 com as imagens embutidas como `data:` depois da conferência do resumo, materiais, adendos e
  assinaturas) ou resumido (título, data, autor, conclusão em texto e vínculos); lista de anexos dos
  subdocumentos incluídos e das entradas incluídas (nome, origem e SHA-256).

## R10. Resumo da composição e reaproveitamento

- **Decision**: o resumo da composição cobre projeto e versão, opções, permissão financeira,
  layout, partes (tipo, id, versão e resumo congelado), entradas do caderno (id, situação, resumo
  assinado e adendos) e pendências; o resumo da trilha mostra os eventos até a geração e não entra
  no resumo da composição (senão nenhum pedido seria reaproveitado, porque o próprio pedido gera
  evento). Um pedido com o mesmo resumo e a mesma natureza (oficial ou rascunho) devolve o documento
  já arquivado, com o evento `fulldoc.reused`.

## R11. Verificação

- **Decision**: o código de verificação do documento completo usa o mesmo alfabeto da 006 (16
  caracteres Crockford) sobre `project:<id>:<versão>:<resumo da composição>:<layout>`; a tela de
  verificação da 006 consulta também os documentos completos (registro de consultas extras na
  app de documentos, sem dependência circular).
