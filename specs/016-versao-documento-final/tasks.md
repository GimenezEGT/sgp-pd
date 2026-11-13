---

description: "Task list for feature 016 — Versionamento do documento final do projeto"
---

# Tasks: Versionamento do documento final do projeto

**Input**: Design documents from `/specs/016-versao-documento-final/`

**Tests**: obrigatórios (constituição VIII); marcador `req("016:…")`; fixtures da 009.

## Phase 1: Foundational

- [ ] T001 Modelo `FinalDocumentVersion` (`AppendOnlyModel`) e `FullDocument.final_version` conforme `data-model.md` ("number sequencial por projeto, a partir de 1; único com project"; reason `approval`, `recomposition`, `reconstruction`), migrações `0003_final_document_version` e `0004_final_version_trigger` e evento `fulldoc.version_created` em `sgp/fulldoc/`
- [ ] T002 `sgp/fulldoc/versioning.py`: nome da parte, composição na ordem do documento, resumo da composição, `register` (numeração com bloqueio da linha do projeto, mudança com versão anterior e nova, evento) e `ensure_current` (recomposição)

## Phase 2: User Story 1 - Versão própria que acompanha as partes (P1) 🎯 MVP

- [ ] T003 [P] [US1] Testes em `tests/fulldoc/test_final_versions.py`: aprovação do projeto gera a versão 01 com TAP e Plano numa só versão; aprovação da Entrada gera a 02 com "Entrada de Projeto: — → 01"; nova versão aprovada gera "01 → 02"; envio, devolução e nova versão em rascunho não mudam a versão; composição com versão, data e resumo de cada parte; evento `fulldoc.version_created`; registro imutável; numeração sequencial sem lacuna em aprovações seguidas; aprovação de Alteração de Projeto também gera versão (FR-001 a FR-005, SC-001)
- [ ] T004 [US1] Chamar `versioning.register` em `approve` e `approve_project` de `sgp/signatures/services.py`, na mesma transação, depois do congelamento

## Phase 3: User Story 3 - Documento completo gerado traz a versão (P1)

- [ ] T005 [P] [US3] Testes: recomposição antes de gerar quando a aprovação foi gravada por fora do fluxo; documento gerado aponta para a versão; nome do arquivo e capa com a versão do documento final e a do projeto; parte "Versões do documento final" no PDF; documento gerado antes da 016 não é reaproveitado para uma versão registrada; rascunho de projeto sem aprovação indica que não há versão do documento final (FR-007, FR-010, SC-002)
- [ ] T006 [US3] Implementar em `sgp/fulldoc/services.py`, `compose.py` e `templates/fulldoc/pdf/document.html` (capa, quadro, nome do arquivo, código de verificação e resumo pela versão do documento final)

## Phase 4: User Story 2 - Rastreabilidade na tela do projeto (P1)

- [ ] T007 [US2] Testes e implementação da seção "Versões do documento final" e da coluna "Versão do documento final" em `sgp/fulldoc/templates/fulldoc/project.html` e na view (FR-006, SC-003)

## Phase 5: User Story 4 - Histórico de versões de cada parte (P2)

- [ ] T008 [US4] Testes e implementação da etiqueta `historico_de_versoes` (`sgp/fulldoc/templatetags/fulldoc_versions.py`, `templates/fulldoc/_part_history.html`) nas telas do subdocumento e do projeto (TAP e Plano): versão, situação, abertura e motivo, aprovação e versões do documento final (FR-008)

## Phase 6: Reconstrução do histórico (FR-009)

- [ ] T009 Testes e implementação de `sgp/fulldoc/history.py` (`rebuild(apps)`: aprovações por projeto em ordem de data; mesmo aprovador em menos de 5 segundos numa só versão; versões "reconstruídas"; idempotente) e da migração `0005_rebuild_history`

## Phase 7: Polish

- [ ] T010 `README.md` (linha da feature 016); rotas sem mudança no contrato
- [ ] T011 Rodar `scripts/verificar.sh`
- [ ] T012 Executar o quickstart na pilha real e registrar em `docs/validacao/016-resultados-execucao.md`

## Dependencies & Execution Order

Foundational → US1 → US3 → US2 → US4 → Reconstrução → Polish.

## Implementation Strategy

MVP: US1 (versão nasce na aprovação, com composição e trilha) e US3 (o documento gerado mostra a
versão); depois a tela do projeto, o histórico das partes e a reconstrução.
