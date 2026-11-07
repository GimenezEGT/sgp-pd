---

description: "Task list for feature 004 — Modelos de formulário versionados e subdocumentos"
---

# Tasks: Modelos de formulário versionados e subdocumentos

**Input**: Design documents from `/specs/004-modelos-subdocumentos/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: obrigatórios (constituição VIII: TDD no schema, nos tipos de campo, no "não aplicável", no fluxo, na migração e nas permissões); marcador `req("004:…")`.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 Incluir `jsonschema` em `pyproject.toml` e `uv.lock` e reconstruir a imagem
- [ ] T002 Criar as apps `sgp/formtemplates` (rotas `/modelos/`, item de navegação "Modelos de formulário" para todos os perfis) e `sgp/subdocuments` (rotas em `/projetos/<id>/subdocumentos/` e `/subdocumentos/`) e registrá-las em `config/settings.py` e `config/urls.py`
- [ ] T003 [P] Criar a migração de dados `sgp/vocab/migrations/0004_seed_subdocumentos.py` com as listas `funcionalidade`, `classificacao-teste`, `automacao`, `usuario`, `classificacao-uso`, `filtro`, `requisito-desempenho` (16), `classe-risco`, `disposicao`, `prazo-transferencia` e `setor-transferencia` de docs/contexto/05-vocabularios.md, em `sgp/vocab/seed.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T004 [P] Escrever testes que falham do JSON Schema e das regras semânticas em `tests/formtemplates/test_schema.py` (definição válida; tipo desconhecido; chave inválida; rótulo de tópico repetido sem diferença de caixa; chave de campo repetida; lista controlada e tipo de cadastro inexistentes; `rows` de `entry_topics` inexistentes) (FR-001 a FR-003)
- [ ] T005 Implementar `sgp/formtemplates/schema.py` conforme `contracts/definicao-modelo.md`
- [ ] T006 Implementar `FormTemplate` (data-model.md: "único por tipo", "um só rascunho por tipo", `published_by` nulo só na carga) em `sgp/formtemplates/models.py`, com migração e gatilho que recusa UPDATE de definição, versão, referência ou tipo em linha publicada (FR-004)
- [ ] T007 [P] Escrever testes que falham de cada tipo de campo em `tests/formtemplates/test_fieldtypes.py` (validação de formato, vazio, resumo para o "Previsto", referências a bloquear, contagem de tabelas, total de coluna numérica)
- [ ] T008 Implementar o registro de tipos de campo em `sgp/formtemplates/fieldtypes.py` (rich_text, text, list, table, vocabulary, reference, attachment, date, number, applicability, derived_table, entry_topics, subdocuments, lots_production, note)
- [ ] T009 Escrever as definições versão 05 dos nove tipos em `sgp/formtemplates/seed_v05.py` a partir de docs/contexto/02-dicionario-documentos.md (com as decisões do esclarecimento: tópico 9 "Classificação de Risco (RDC 830/2023)", Análise Crítica com 3 tópicos, Saída 1 a 12 com itens 6 e 7 só MAPA) e a migração de dados que as publica; teste em `tests/formtemplates/test_seed.py` (SC-001)
- [ ] T010 Implementar `Subdocument` e `FlowAuthorization` (append-only) em `sgp/subdocuments/models.py` conforme data-model.md ("único por projeto, tipo e número"), com migração e gatilho de imutabilidade da autorização
- [ ] T011 [P] Registrar os eventos de `contracts/eventos-auditoria.md` em `sgp/formtemplates/event_types.py`, `sgp/subdocuments/event_types.py` e `projects.version_changed` em `sgp/projects/event_types.py`
- [ ] T012 Implementar `sgp/subdocuments/permissions.py` (editores: membros Analista/Líder e Gestor de P&D em projeto aberto; consulta pela regra única) e a política de arquivos dos anexos de subdocumento; testes em `tests/subdocuments/test_permissions.py` (FR-008, FR-014)

**Checkpoint**: Foundation ready

---

## Phase 3: User Story 1 - Cadastrar o modelo de formulário (Priority: P1) 🎯 MVP

**Goal**: Qualidade cadastra, confere e publica modelos.

**Independent Test**: criar rascunho, editar a definição, pré-visualizar e publicar; rótulo repetido recusado; outro perfil barrado.

- [ ] T013 [P] [US1] Testes em `tests/formtemplates/test_templates.py` (rascunho da próxima versão com cópia da vigente; edição de metadados e definição com evento; publicação recusada com definição inválida e mensagem do tópico; numeração calculada; um só rascunho por tipo; perfil sem Qualidade → 403 e evento) (FR-001, FR-003, FR-005)
- [ ] T014 [US1] Implementar `sgp/formtemplates/services.py` (`create_draft`, `update_draft` com `row_version`, `publish`, `current_template`) e as telas lista, detalhe com pré-visualização, edição e publicação em `views.py`, `forms.py`, `templates/formtemplates/`

---

## Phase 4: User Story 2 - Nova versão sem alterar documentos iniciados (Priority: P1)

**Goal**: versão 06 não muda documentos da 05; gestor migra rascunho.

**Independent Test**: documento na 05, publicar 06, conferir documento e documento novo; migrar.

- [ ] T015 [P] [US2] Testes em `tests/subdocuments/test_template_versions.py` (documento iniciado continua na 05; novo nasce na vigente; vigência futura; modelo publicado imutável pelo serviço e pelo banco; migração pelo Gestor com motivo mantém dados compatíveis e guarda o resto; migração de aprovado ou por outro perfil recusada) (FR-004, FR-007, SC-002)
- [ ] T016 [US2] Implementar `migrate_template` em `sgp/subdocuments/services.py` e a exibição dos dados não migrados

---

## Phase 5: User Story 3 - Criar e preencher subdocumentos (Priority: P1)

**Goal**: formulário montado do modelo, validação, trilha, numeração, concorrência.

**Independent Test**: criar e preencher a Formulação com insumos e anexo; conferir trilha e numeração.

- [ ] T017 [P] [US3] Testes em `tests/subdocuments/test_subdocuments.py` (criação em rascunho, versão 01 e modelo vigente; um por tipo e Alterações numeradas; gravação conferida contra o modelo com rascunho incompleto; "não aplicável" sem justificativa ou com campos preenchidos recusado; evento com antes e depois; edição simultânea recusada; sem acesso ao projeto → 403 registrado; lote de outro projeto recusado; referências por versão; anexos com política do projeto) (FR-008 a FR-014, SC-004)
- [ ] T018 [P] [US3] Testes em `tests/subdocuments/test_numbering.py` (tópicos numerados entre os visíveis; tabelas "Tabela 01, 02" em ordem; itens MAPA ocultos não contam) (FR-011)
- [ ] T019 [US3] Implementar `sgp/subdocuments/services.py` (`create_subdocument`, `save_subdocument`), `parsing.py`, `rendering.py` e `numbering.py`
- [ ] T020 [US3] Implementar as telas lista do projeto, criação, detalhe e edição com HTMX (nova linha de tabela e busca de cadastros com seleção) em `sgp/subdocuments/views.py`, `urls.py`, `templates/subdocuments/` e o modo de seleção na busca de `sgp/catalog/views.py`
- [ ] T021 [P] [US3] Testes e implementação da aprovação provisória em `tests/subdocuments/test_approval.py` e `services.py` (só Gestor de P&D ≠ criador; completude; bloqueio da edição; bloqueio das versões de cadastros referenciadas) (FR-015)
- [ ] T022 [P] [US3] Testes e implementação do fluxo em `tests/subdocuments/test_flow.py` e `sgp/subdocuments/flow.py` (Entrada aprovada exigida por todos os outros, sem dispensa; aviso fora da ordem nos demais; autorização do Gestor com motivo usada uma vez; Alteração exige Entrada aprovada) (FR-016)
- [ ] T023 [P] [US3] Teste de desempenho em `tests/subdocuments/test_performance.py`: gravar subdocumento com 100 linhas de tabela em < 2 s (SC-005)

---

## Phase 6: User Story 4 - Entrada com formulário opcional (Priority: P1)

**Goal**: 13 tópicos, formulário opcional e "aplica / não se aplica".

**Independent Test**: preencher a Entrada e recusar "não se aplica" sem justificativa.

- [ ] T024 [P] [US4] Testes em `tests/subdocuments/test_entry.py` (13 tópicos numerados e formulário opcional; seleções das listas controladas; requisito "não se aplica" sem justificativa recusado; tópico 9 pré-preenchido da classe de risco do projeto) (FR-017)
- [ ] T025 [US4] Implementar o campo `applicability` no formulário e no detalhe e o pré-preenchimento do projeto em `sgp/subdocuments/rendering.py` e `services.py`

---

## Phase 7: User Story 5 - Validação e Verificação Final derivadas (Priority: P2)

**Goal**: pendências e checklist nascem da Entrada aprovada.

**Independent Test**: aprovar Entrada; criar Validação e Verificação Final e conferir as linhas.

- [ ] T026 [P] [US5] Testes em `tests/subdocuments/test_derived.py` (pendências por requisito "aplica" e "não se aplica" com justificativa; Verificação Final só com Entrada aprovada, uma linha por requisito de entrada e "Previsto" igual ao resumo da Entrada; disposição ≠ Aprovado sem justificativa recusada; atualização a partir da Entrada preserva o preenchido) (FR-018, FR-019, SC-003)
- [ ] T027 [US5] Implementar `sgp/subdocuments/derived.py` e a ação de atualizar derivados

---

## Phase 8: User Story 6 - Saída de Projeto (Priority: P2)

- [ ] T028 [P] [US6] Testes em `tests/subdocuments/test_exit.py` (itens MAPA só em projeto MAPA e não exigidos no ANVISA; setores da lista controlada; novas matérias-primas e embalagens só de insumos novos do tipo certo) (FR-020)
- [ ] T029 [US6] Implementar os filtros de referência (`filter`) e a visibilidade por órgão regulador em `sgp/formtemplates/fieldtypes.py` e `sgp/subdocuments/rendering.py`

---

## Phase 9: User Story 7 - Alteração de Projeto (Priority: P2)

- [ ] T030 [P] [US7] Testes em `tests/subdocuments/test_change.py` (versão alterada e nova versão; análise de risco obrigatória na aprovação; aprovação sobe a versão do projeto com evento; subdocumentos afetados marcados para revisão com a Alteração de origem) (FR-021)
- [ ] T031 [US7] Implementar a aprovação da Alteração em `sgp/subdocuments/services.py` e `bump_version` em `sgp/projects/services.py`

---

## Phase 10: Polish & Cross-Cutting Concerns

- [ ] T032 Incluir as rotas de `contracts/rotas-ui.md` no contrato de `tests/core/test_route_scan.py`
- [ ] T033 [P] Atualizar `README.md` (feature 004) e o detalhe do projeto com o acesso aos subdocumentos
- [ ] T034 Rodar `scripts/verificar.sh` (ruff, testes, cobertura, matriz) e corrigir o que faltar
- [ ] T035 Executar o quickstart na pilha real (curl) e registrar em `docs/validacao/004-resultados-execucao.md`

---

## Dependencies & Execution Order

- Setup → Foundational → US1 → US2 → US3 → US4 → US5 → US6 → US7 → Polish.
- T005 e T008 antes do seed (T009); T010 antes de T012 e das histórias de subdocumento.
- US5 depende da aprovação (T021) e da Entrada (US4); US7 depende da aprovação.

## Parallel Example: User Story 3

```bash
Task: "Testes em tests/subdocuments/test_subdocuments.py"
Task: "Testes em tests/subdocuments/test_numbering.py"
```

## Implementation Strategy

MVP = US1 a US4 (modelos versão 05 publicados e subdocumentos preenchíveis, com a Entrada); US5 a
US7 completam as derivações e a Alteração.

## Notes

- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each logical group
