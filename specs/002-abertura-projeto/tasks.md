---

description: "Task list for feature 002 — Abertura de projeto: TAP e Plano de Negócios"
---

# Tasks: Abertura de projeto — TAP e Plano de Negócios

**Input**: Design documents from `/specs/002-abertura-projeto/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: obrigatórios (constituição VIII: TDD em regras, cálculos e permissões); marcador `req("002:…")`.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 Criar a app `sgp/vocab` (`Vocabulary`: "code slug único", "version inteiro"; `Term`: "code/label únicos por vocabulário", `position`, `is_active`, sem exclusão) com migrações `0001_initial` e `0002_seed` (tecnologia e tipo-subdocumento de data-model.md) e registrá-la em `config/settings.py`
- [ ] T002 Criar a app `sgp/projects` (apps, urls em `/projetos/`, item de navegação "Projetos" para todos os perfis em `sgp/core/navigation.py`) e as configurações `PROJECT_CODE_PREFIX` (padrão `PD`) e `FINANCIAL_DATA_PROFILES` (vazio) em `config/settings.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T003 [P] Escrever testes que falham da carga das listas em `tests/vocab/test_vocab.py` (termos presentes, sem exclusão, `active_terms`)
- [ ] T004 [P] Escrever testes e implementar `changed_fields(before, after)` em `sgp/core/diff.py` e `tests/core/test_diff.py`
- [ ] T005 Escrever testes que falham e implementar o mascaramento da trilha em `sgp/audit/masking.py` (registro por tipo de evento, chaves sensíveis e regra de visibilidade por projeto) aplicado em `sgp/audit/views.py` e `sgp/audit/exports.py`; testes em `tests/audit/test_masking.py`
- [ ] T006 Implementar os modelos de `sgp/projects/models.py` conforme data-model.md (`Project` com "code texto(20), único, nulo até a aprovação" e "version nulo até a aprovação", `ProjectCharter` com listas JSONB, `BusinessPlan` com Decimal(14,2) ≥ 0, `AnnualForecast` "year_index 1 a 5 único por plano", `ProjectMember` com vínculo ativo único, `Milestone` com cancelamento, `ProjectDecision` append-only, `ProjectCodeSequence`) e a migração
- [ ] T007 [P] Escrever testes e implementar `BRLMoneyField` em `sgp/projects/fields.py` e o filtro `brl` em `sgp/core/templatetags/sgp.py`; testes em `tests/projects/test_money.py` (FR-009)
- [ ] T008 Escrever testes que falham e implementar `sgp/projects/permissions.py` (`get_project_or_deny`, `can_edit_project`, `can_view_financials`) e `Project.is_member`; testes em `tests/projects/test_permissions.py` (FR-003, FR-010)
- [ ] T009 [P] Registrar os eventos de `contracts/eventos-auditoria.md` em `sgp/projects/event_types.py` e as chaves sensíveis no mascaramento

**Checkpoint**: Foundation ready

---

## Phase 3: User Story 1 - Criar o projeto em rascunho (Priority: P1) 🎯 MVP

**Goal**: líder cria rascunho com dados do produto e regime deduzido.

**Independent Test**: criar projeto como líder; Analista sem acesso global não abre o rascunho.

- [ ] T010 [P] [US1] Testes em `tests/projects/test_create.py` (FR-001 criação e evento; FR-002 regime e MAPA sem classe; FR-003 rascunho invisível para Analista; perfil sem permissão não cria; FR-019 edição do produto gera evento com valor anterior e novo)
- [ ] T011 [US1] Implementar `create_project` e `update_product` (diff e `row_version`) em `sgp/projects/services.py`
- [ ] T012 [US1] Implementar formulários, views e templates de novo projeto, detalhe e edição do produto em `sgp/projects/forms.py`, `views.py`, `templates/projects/`

---

## Phase 4: User Story 2 - Preencher o TAP (Priority: P1)

**Goal**: TAP com listas, tabelas, equipe e marcos, com trilha.

**Independent Test**: preencher TAP, incluir membros e marcos e conferir eventos com valor anterior e novo.

- [ ] T013 [P] [US2] Testes em `tests/projects/test_charter.py` (FR-004 gravação e diff; FR-005 equipe com vigência e encerramento com motivo; FR-006 marcos, data realizada válida, cancelamento; FR-013 bloqueio quando submetido; FR-020 gravação concorrente recusada)
- [ ] T014 [US2] Implementar `update_charter`, `add_member`, `end_member`, `add_milestone`, `update_milestone` e `cancel_milestone` em `sgp/projects/services.py`
- [ ] T015 [US2] Implementar as telas do TAP (listas por linha, formsets de riscos e partes interessadas), da equipe e dos marcos em `sgp/projects/forms.py`, `views.py` e templates

---

## Phase 5: User Story 3 - Plano de Negócios com dados financeiros protegidos (Priority: P1)

**Goal**: plano completo, total calculado e permissão por campo.

**Independent Test**: plano salvo pelo líder; membro e Qualidade não veem financeiros em tela, URL direta e trilha.

- [ ] T016 [P] [US3] Testes em `tests/projects/test_business_plan.py` (FR-007 campos e fonte única; FR-008 total calculado; FR-009 formato BR, negativos, faixas; FR-010 mascaramento no detalhe, 403 na edição, trilha e exportação mascaradas; SC-002; FR-020 gravação concorrente do plano recusada)
- [ ] T017 [US3] Implementar `update_business_plan` (previsões e diff com chaves financeiras) e a apresentação mascarada em `sgp/projects/services.py` e `sgp/projects/presentation.py`
- [ ] T018 [US3] Implementar formulário, view e template do Plano de Negócios e a seção do detalhe

---

## Phase 6: User Story 4 - Submeter, aprovar ou devolver (Priority: P1)

**Goal**: máquina de estados, pendências, código anual sem colisão e acesso da equipe.

**Independent Test**: submeter, devolver, corrigir, aprovar; conferir código, versão, acesso e histórico.

- [ ] T019 [P] [US4] Testes em `tests/projects/test_workflow.py` (FR-011 transições válidas e inválidas; FR-012 pendências; FR-013 bloqueio; FR-014 comentário obrigatório e líder não aprova; FR-015 código, versão e acesso; FR-016 histórico; FR-017 bloqueio após aberto)
- [ ] T020 [P] [US4] Testes em `tests/projects/test_code_sequence.py` (SC-003 aprovações concorrentes com códigos distintos e consecutivos; virada de ano; prefixo configurável)
- [ ] T021 [US4] Implementar `sgp/projects/workflow.py` (transições, `next_project_code` com `INSERT … ON CONFLICT … RETURNING`) e `sgp/projects/completeness.py` (pendências)
- [ ] T022 [US4] Implementar views e templates de submeter, aprovar e devolver, pendências e histórico de decisões

---

## Phase 7: User Story 5 - Lista de projetos com filtros (Priority: P2)

**Goal**: lista filtrável respeitando acesso e permissão financeira.

**Independent Test**: filtros por status, líder e produto; Analista vê só os seus.

- [ ] T023 [P] [US5] Testes em `tests/projects/test_list.py` (FR-018 filtros e visibilidade; coluna de custo só com permissão; SC-005 lista de 200 projetos em < 2 s)
- [ ] T024 [US5] Implementar a lista com filtros em `sgp/projects/views.py` e `templates/projects/list.html`

---

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T025 Incluir as rotas de projetos no contrato de `tests/core/test_route_scan.py` (perfis exigidos e acesso por projeto)
- [ ] T026 Trocar o filtro `projeto` da trilha por lista de projetos em `sgp/audit/forms.py`, com teste
- [ ] T027 Rodar `scripts/verificar.sh` (ruff, testes, cobertura, matriz) e corrigir o que faltar
- [ ] T028 Executar o quickstart na pilha real (curl) e registrar em `docs/validacao/002-resultados-execucao.md`

---

## Dependencies & Execution Order

- Setup → Foundational → US1 → US2 → US3 → US4 → US5 → Polish (um desenvolvedor, em ordem de prioridade).
- US2, US3 e US4 dependem do projeto criado na US1; US4 depende das pendências que US2 e US3 preenchem.

## Parallel Example: User Story 4

```bash
Task: "Testes em tests/projects/test_workflow.py"
Task: "Testes em tests/projects/test_code_sequence.py"
```

## Implementation Strategy

MVP = US1 a US4 (projeto aberto de ponta a ponta); US5 completa a visão do Gestor.

## Notes

- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each logical group
