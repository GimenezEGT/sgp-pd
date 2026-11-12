# Research: Caderno de laboratório eletrônico

## R1. Editor de texto formatado

- **Decision**: editor próprio em `sgp/notebook/static/notebook/editor.js` (arquivo estático, sem
  biblioteca externa nem etapa de build): cada `textarea[data-rich]` ganha uma barra (negrito,
  itálico, sublinhado, sobrescrito, subscrito, lista, lista numerada, título, tabela, limpar
  formatação) e uma área `contenteditable`; o HTML volta para o `textarea` a cada alteração. Sem
  JavaScript, o `textarea` continua utilizável com texto simples, convertido em parágrafos e listas
  ("- ") como o texto formatado da 004.
- **Rationale**: a CSP da aplicação não aceita estilos nem scripts inline, a intranet não usa CDN e o
  caderno precisa de sobrescrito/subscrito, tabelas e imagens coladas; um editor pequeno sobre
  `contenteditable` cobre isso sem dependência de front-end.
- **Alternatives considered**: Trix/Quill/TipTap (estilos injetados ou build de front-end, muito
  mais código que o necessário); só o texto simples da 004 (não atende tabelas nem colagem de
  imagens pedidas no plano).

## R2. Sanitização no servidor por lista branca

- **Decision**: `nh3` (ligação Python do ammonia) em `sgp/notebook/richtext.py`, aplicado a cada
  gravação e de novo na exibição. Tags aceitas: `p`, `br`, `strong`, `b`, `em`, `i`, `u`, `s`, `sub`,
  `sup`, `ul`, `ol`, `li`, `h3`, `h4`, `blockquote`, `pre`, `table`, `thead`, `tbody`, `tr`, `th`,
  `td`, `img`. Atributos: `img[src, alt]`, `td`/`th[colspan, rowspan]`. `img` só com `src` igual a
  `/arquivos/<id>/` de um anexo da própria entrada; qualquer outra imagem, link, estilo, classe,
  evento ou script é removido (o conteúdo de `script` e `style` também). Contrato em
  `contracts/conteudo-assinado.md`.
- **Rationale**: lista branca é a forma segura de aceitar HTML do usuário; o ammonia é mantido e
  rápido; reaplicar na exibição protege contra dado gravado por outro caminho.
- **Alternatives considered**: `bleach` (descontinuado); escapar tudo (perde a formatação).

## R3. Imagens coladas e anexos

- **Decision**: colar ou arrastar uma imagem no editor envia o arquivo por `fetch` (com o token
  CSRF) para `/caderno/entradas/<id>/anexos/`, que grava pelo `store_upload` da 003 (PNG ou JPEG,
  limite `FILE_MAX_MB`, resumo SHA-256) como anexo da entrada marcado "no texto" e devolve o
  endereço `/arquivos/<id>/`, inserido como `<img>`. Os demais anexos (PDF, PNG, JPEG, CSV, XLSX)
  vão pelo formulário de anexos. A leitura passa pela rota de download da 003, que confere o resumo
  a cada leitura; a política de acesso do caderno entrega o arquivo a quem acessa o projeto.
  Por isso a entrada nasce primeiro (título, modelo e relevância) e o texto é preenchido em seguida.
- **Rationale**: uma única forma de guardar arquivo (hash, limite, tipos) e de entregá-lo.

## R4. Entrada, numeração e situação

- **Decision**: número sequencial por projeto (bloqueio da linha do projeto na criação; único por
  projeto), data e hora de criação do servidor (`timezone.now()`), situação gravada `open`,
  `signed` ou `witnessed`; "atrasada" (aberta há mais que `NOTEBOOK_SIGN_DAYS`, padrão 7) e
  "aguardando testemunha" (assinada e relevante) são derivadas na consulta.
- **Rationale**: a situação derivada acompanha a mudança do prazo configurado sem regravar entradas.

## R5. Bloqueio da entrada assinada

- **Decision**: o serviço recusa gravação, material e anexo em entrada que não está aberta; no banco,
  um gatilho recusa alterar os campos de conteúdo de entrada não aberta e incluir ou alterar
  materiais e anexos de entrada não aberta. Adendo e assinatura são somente de inclusão
  (`AppendOnlyModel` com gatilho de imutabilidade). Relevância e situação continuam alteráveis pelos
  serviços (marcar relevância, testemunhar), sempre com evento.

## R6. Assinatura do autor, da testemunha e dos adendos

- **Decision**: reautenticação da 005 (`sgp.signatures.reauth.reauthenticate`, fora da transação),
  com as mesmas tentativas e bloqueio. A assinatura (`NotebookSignature`) guarda papel (autor ou
  testemunha), pessoa, data e hora do servidor e o resumo SHA-256 do conteúdo canônico
  (`sgp.signatures.canonical.content_hash`). A testemunha precisa acessar o projeto, ser diferente do
  autor e a entrada precisa ser relevante e estar assinada; o resumo recalculado tem de conferir com
  o da assinatura do autor. O adendo nasce assinado: texto sanitizado, pessoa, data e hora e resumo
  próprio. A tela de detalhe confere os resumos e avisa se algo não confere.
- **Decision (adendo)**: pode acrescentar adendo quem pode criar entradas no projeto (o autor ou
  outro editor do projeto); o adendo mostra quem o fez e assinou.
- **Alternatives considered**: reaproveitar o modelo `Signature` da 005 (amarrado às etapas
  elaboração, revisão e aprovação de documentos; o caderno tem papéis próprios).

## R7. Materiais pela versão do cadastro

- **Decision**: `EntryMaterial` com o tipo (lote, insumo, amostra) e a chave estrangeira para a
  versão do registro (`Lot`, `Material`, `Sample`), resolvida pelo código entre os vigentes e ativos
  (`available()`), lote só do mesmo projeto; o código fica copiado para exibição e busca. Retirada só
  com a entrada aberta e lógica (quem e quando).

## R8. Vínculos nos dois sentidos

- **Decision**: `NotebookLink` com o alvo (subdocumento, lote ou estudo do mesmo projeto, uma chave
  estrangeira preenchida), o tipo (`related` ou `promoted`), quem ligou e quando, e retirada lógica
  com motivo (o vínculo de promoção não é retirado, porque registra a origem dos dados do estudo).
  Os vínculos podem ser feitos com a entrada assinada. O subdocumento, o estudo e o lote mostram as
  entradas ligadas por um trecho de template comum.

## R9. Promoção para estudo

- **Decision**: de um anexo CSV ou XLSX da entrada, o editor escolhe um estudo em elaboração do
  mesmo projeto e o mapeamento das colunas (o salvo por equipamento da 007, se houver); os bytes são
  lidos com conferência do resumo e passam por `sgp.studies.importing.preview` e `confirm`, na mesma
  transação em que nasce o vínculo `promoted` (com o anexo). Eventos: `notebook.promoted` na entrada
  e `studies.imported` no estudo, com a entrada de origem.

## R10. Busca e linha do tempo

- **Decision**: a entrada e o adendo guardam `search_text` (texto puro sem acentos: título e textos
  da entrada, códigos dos materiais; texto do adendo) e uma coluna gerada
  `to_tsvector('portuguese', search_text)` com índice GIN; a consulta remove os acentos e usa
  `websearch_to_tsquery('portuguese', …)`. Filtros: projeto, lote (materiais e vínculos), amostra,
  pesquisador, período, situação e "aberta há mais de N dias"; só projetos acessíveis
  (`accessible_projects`). Linha do tempo por data decrescente, 20 por página, "carregar mais" com
  HTMX (sem script inline).
- **Rationale**: busca em português sem serviço extra; tirar os acentos dos dois lados faz "solucao"
  achar "solução".
- **Alternatives considered**: `unaccent` no banco (função não imutável, não serve em coluna
  gerada); Elasticsearch (serviço novo sem necessidade).

## R11. Modelos de entrada

- **Decision**: `EntryTemplate` versionado por linhagem (como os cadastros da 003): nome do tipo de
  experimento e textos padrão de objetivo, hipótese, procedimento, resultados e conclusão
  (sanitizados); cada alteração cria nova versão vigente com motivo; desativar tira da escolha. A
  entrada copia os textos ao nascer e guarda a versão usada. Mantidos por Qualidade/AR e Gestor de
  P&D, fora do ciclo da 013 (esclarecimento provisório).

## R12. Permissões e dados pessoais

- **Decision**: criar entrada e adendo e fazer vínculos: editores do projeto aberto
  (`sgp.subdocuments.permissions.can_edit`: membros com perfil Analista/Pesquisador ou Líder e o
  Gestor de P&D); editar e assinar: só o autor; testemunhar: quem acessa o projeto, menos o autor;
  relevância: o autor ou o Gestor de P&D, até haver testemunha; ver e buscar: regra única de acesso
  ao projeto (equipe, Gestor de P&D, Qualidade/AR e Administrador). Negação registrada por
  `deny_access`. A regra de LGPD das amostras (003) não se aplica aos textos do caderno; as amostras
  entram pelo código do cadastro.

## R13. Testes

- **Decision**: testes por requisito (`req("008:FR-…")`), sanitização com casos maliciosos (script,
  evento, estilo, imagem externa, imagem de outra entrada), bloqueio no serviço e no gatilho, busca
  em português com e sem acento, desempenho com 1.000 entradas (< 2 s) e promoção com vínculo nos dois
  sentidos. Os dados dos testes são fictícios e criados nos próprios testes.
