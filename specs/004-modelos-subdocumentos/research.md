# Research: Modelos de formulário versionados e subdocumentos

## R1. Nomes e apps

"formularios" → `sgp/formtemplates` (`FormTemplate`); "subdocumentos" → `sgp/subdocuments`
(`Subdocument`, `FlowAuthorization`). Rotas em português: `/modelos/` e
`/projetos/<id>/subdocumentos/`.

## R2. Definição do modelo em JSON com JSON Schema próprio

- **Decision**: a definição (capa e tópicos) fica em JSONB e é validada pelo JSON Schema próprio
  (`jsonschema`, draft 2020-12) e por regras semânticas: chaves e rótulos de tópico únicos, chaves
  de campo únicas no tópico, listas controladas e tipos de cadastro existentes. Metadados (tipo,
  versão do formulário, referência, vigência, situação) são colunas. Formato no contrato
  `contracts/definicao-modelo.md`.
- **Rationale**: pedido do plano; permite nova versão sem programação e validação objetiva.
- **Alternatives considered**: tabelas relacionais de tópicos e campos (muitas tabelas e
  migrações a cada tipo novo).

## R3. Edição do modelo pela Qualidade

- **Decision**: rascunho de nova versão nasce como cópia da vigente; a Qualidade edita metadados
  num formulário e a definição num editor de texto JSON com validação e pré-visualização da capa e
  dos tópicos numerados. Publicar exige definição válida.
- **Rationale**: entrega o "cadastro, não programação" sem um construtor visual aninhado; a
  feature 013 trata a revisão controlada (comparação, aprovação, vigência).
- **Alternatives considered**: construtor visual com formsets aninhados (alto custo, fora do MVP).

## R4. Imutabilidade do modelo publicado

- **Decision**: serviço recusa edição de modelo publicado e um gatilho no banco recusa UPDATE que
  mude definição, versão, referência ou tipo de linha publicada; publicar fixa `published_at/by`.
- **Rationale**: FR-004 com a mesma defesa em profundidade da trilha.

## R5. Versão vigente

- **Decision**: vigente de um tipo numa data = a publicada mais recente com `valid_from` ≤ data.
  Documento novo grava o modelo vigente na criação; publicar não toca documentos existentes.

## R6. Dados do subdocumento

- **Decision**: `data = {"topics": {<chave>: {"na": bool, "justification": str, "values": {<campo>:
  valor}}}}`. Valores: texto (str), lista (lista de str), tabela (lista de objetos por coluna),
  seleção (código do termo ou lista de códigos), referência (id da versão do cadastro ou lista),
  anexo (lista de ids de `StoredFile`), data (ISO), número (texto decimal). Validação a cada
  gravação (tipos e formatos); completude (obrigatórios e "não aplicável" justificado) na
  aprovação. Controle otimista com `row_version`.
- **Rationale**: FR-009, FR-010, FR-012; JSONB conferido contra a definição usada.

## R7. Formulário montado no servidor

- **Decision**: renderização por tipo de campo (`templates/subdocuments/fields/<tipo>.html`) e
  leitura do POST por nomes `t__<tópico>__<campo>[__<linha>__<coluna>]`. Tabelas: linhas
  existentes mais linhas em branco e botão HTMX "Adicionar linha". Referências: busca enquanto
  digita (endpoint da 003 com `campo=`) que devolve opções marcáveis; as escolhidas ficam como
  caixas marcadas (desmarcar retira). Células de tabela que referenciam cadastro recebem o código
  (insumo, lote, amostra, norma), resolvido para a versão vigente na gravação.
- **Rationale**: sem JavaScript próprio (CSP `default-src 'self'`, HTMX sem eval); estruturas
  dinâmicas sem formsets aninhados.

## R8. Tipos derivados

- **Decision**: `derived_table` com `source`:
  - `entry_topics` — Verificação Final: uma linha por tópico da Entrada listado no modelo, com
    "Previsto" = resumo do tópico na Entrada aprovada e colunas editáveis do modelo;
  - `entry_requirements` — Validação (pendências) e Análise Crítica: uma linha por requisito
    "aplica" da Entrada aprovada, com o critério de aceitação; os "não se aplica" listados com a
    justificativa;
  - `milestones` — Análise Crítica: marcos planejados × realizados do projeto (só leitura).
  As linhas derivadas são copiadas na criação e podem ser atualizadas a partir da Entrada aprovada
  (ação registrada), preservando o que foi preenchido em cada linha.
  `applicability` — tabela "aplica / não se aplica" da Entrada, com a lista controlada dos 16
  requisitos. `entry_topics` e `subdocuments` — seleção de tópicos da Entrada e de subdocumentos
  do projeto (Alteração). `lots_production` — responsável e local dos lotes referenciados
  (Lote Piloto, tópico 5). `note` — texto fixo do modelo.

## R9. Fluxo e aprovação provisória

- **Decision**: ordem recomendada fixa (Entrada → Formulação → Lote Piloto → RAPD → Análise
  Crítica → Validação → Verificação Final → Saída); antecessor não aprovado exige
  `FlowAuthorization` do Gestor de P&D com motivo. Alteração exige a Entrada aprovada; Verificação
  Final exige a Entrada aprovada (sem autorização que dispense). Aprovação provisória: Gestor de
  P&D diferente do criador, completude conferida, documento bloqueado e cadastros referenciados
  bloqueados (`catalog.versioning.lock_version`).

## R10. Alteração de Projeto

- **Decision**: guarda `changed_version` (versão atual do projeto) e `new_version` (seguinte) na
  criação; análise de risco obrigatória (texto ou anexo); na aprovação, `Project.version` sobe
  (evento `projects.version_changed`) e os subdocumentos escolhidos recebem a marca de revisão
  (`review_requested_by` = a Alteração).

## R11. Migração de documento para a versão vigente

- **Decision**: só rascunho, só Gestor de P&D, com motivo. Tópicos e campos com a mesma chave e
  tipo compatível passam; o resto vai para `unmapped_data`, exibido no documento; evento com as
  versões e o que não migrou.

## R12. Texto formatado

- **Decision**: texto com parágrafos e listas simples ("- " no início da linha), guardado como
  texto e exibido escapado com `<p>`/`<ul>` gerados no servidor; sem HTML do usuário.
- **Rationale**: segurança (sem sanitizador de HTML nesta feature) e simplicidade; o editor rico
  da feature 008 pode ser reaproveitado depois.

## R13. Numeração

- **Decision**: tópicos numerados pela ordem entre os visíveis no projeto (itens MAPA ocultos não
  contam); tabelas com conteúdo numeradas em sequência no documento ("Tabela 01 – <rótulo>").
