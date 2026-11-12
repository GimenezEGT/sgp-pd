---

description: "Task list for feature 007 — Estudos de desempenho e estabilidade com cálculo automático"
---

# Tasks: Estudos de desempenho e estabilidade com cálculo automático

**Input**: Design documents from `/specs/007-estudos-calculo/`

**Tests**: obrigatórios (constituição VI e VIII: cálculo com vetores de referência e TDD); marcador `req("007:…")`.

## Phase 1: Setup

- [ ] T001 Acrescentar `scipy` (runtime) e `hypothesis` (desenvolvimento) em `pyproject.toml` e `uv.lock`; criar a app `sgp/studies` com as rotas `/estudos/` e a lista controlada `tipo-estudo` (14 tipos) em `sgp/vocab/migrations/0005_seed_estudos.py` e `sgp/vocab/seed.py`

## Phase 2: Foundational

- [ ] T002 [P] Escrever testes e implementar `sgp/studies/stats.py` (V1 a V8 e propriedades com hypothesis; não calculáveis) em `tests/studies/test_stats.py` (FR-007, FR-010, FR-011, FR-012, SC-001)
- [ ] T003 [P] Escrever testes e implementar `sgp/studies/profiles.py` conforme `contracts/perfis-calculo.md` (métricas por tipo, grupos, critério atendido) em `tests/studies/test_profiles.py` (FR-007, FR-009)
- [ ] T004 Implementar `Study` e `ImportMapping` com migração e eventos em `sgp/studies`

## Phase 3: User Stories 1 a 3 - Estudo, critério, resultados e cálculo (P1) 🎯 MVP

- [ ] T005 [P] Testes em `tests/studies/test_services.py` (tipo controlado e com perfil; critério congelado depois da primeira linha; linhas numeradas com cadastros válidos; código inexistente recusado; resultados recalculados; editores do projeto; sem campo de valor calculado; 500 medidas em < 2 s) (FR-001 a FR-005, FR-008, FR-017, FR-018, SC-004)
- [ ] T006 Implementar `sgp/studies/services.py`, as telas de lista, criação e detalhe com a tabela de linhas e os resultados
- [ ] T007 [P] Testes em `tests/studies/test_importing.py` (CSV com `;` e `,`, XLSX, mapeamento salvo por equipamento, linhas recusadas com motivo, pré-visualização assinada, 1.000 linhas em < 10 s) (FR-006, SC-005)
- [ ] T008 Implementar `sgp/studies/importing.py` e a tela de importação

## Phase 4: User Story 4 - Não aplicável (P2)

- [ ] T009 Testes e implementação do não aplicável com justificativa, exclusivo com linhas, em `tests/studies/test_services.py` (FR-013, SC-002)

## Phase 5: User Story 5 - Documentos e versões (P2)

- [ ] T010 [P] Testes em `tests/studies/test_documents.py` (vínculo ao tópico do RAPD ou da Validação; tabelas numeradas e conclusão no documento gerado; não aplicável com justificativa no documento; resumo assinado cobre os estudos; aprovação bloqueia; editar bloqueado recusado; nova versão com motivo preserva a anterior no aprovado) (FR-014 a FR-016, SC-003)
- [ ] T011 Integrar `sgp/signatures/documents.py` (conteúdo canônico), `sgp/subdocuments/services.py` (bloqueio na aprovação e lista no detalhe) e `sgp/documents/content.py` (tabelas no documento)

## Phase 6: Polish

- [ ] T012 Rotas no contrato de `tests/core/test_route_scan.py`; `README.md` (feature 007)
- [ ] T013 Rodar `scripts/verificar.sh`
- [ ] T014 Executar o quickstart na pilha real e registrar em `docs/validacao/007-resultados-execucao.md`

## Dependencies & Execution Order

Setup → Foundational → US1–US3 → US4 → US5 → Polish.
