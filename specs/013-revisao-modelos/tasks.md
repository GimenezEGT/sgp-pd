---

description: "Task list for feature 013 — Revisão controlada dos modelos"
---

# Tasks: Revisão controlada dos modelos de documentos e subdocumentos

**Input**: Design documents from `/specs/013-revisao-modelos/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: obrigatórios (constituição VIII: TDD no ciclo, nas permissões, na vigência e na adulteração); marcador `req("013:…")`.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

- [ ] T001 Criar a app `sgp/revisions` (rotas `/revisoes-modelos/`, item de navegação "Revisões de modelos" para todos os perfis) e a tarefa diária `sgp.revisions.record_due` no agendador do worker em `config/settings.py`

## Phase 2: Foundational

- [ ] T002 Implementar o mixin `RevisableTemplate` e os modelos `TemplateStep`, `TemplateSignature` e `TemplateRetirement` (data-model.md) com migrações em `sgp/revisions`, `sgp/formtemplates` e `sgp/documents` (situação `discarded`), gatilhos somente de inclusão e eventos de `contracts/eventos-auditoria.md`
- [ ] T003 [P] Escrever testes e implementar `sgp/revisions/diff.py` (achatamento por chave; incluídos, retirados e alterados; sem mudança) em `tests/revisions/test_diff.py` (FR-007, FR-018)
- [ ] T004 Implementar `sgp/revisions/adapters.py` (formulário e layout: família, versões, vigente, conteúdo e resumo, publicação interna, uso por versão)

## Phase 3: User Stories 1 e 2 - Elaborar, enviar, devolver e aprovar (P1) 🎯 MVP

- [ ] T005 [P] [US1] [US2] Testes em `tests/revisions/test_cycle.py` (abrir nasce da vigente sem mudá-la; uma revisão em andamento; envio exige motivo e impacto, recusa sem mudança e com rótulo repetido; enviada não muda; devolução exige comentário e volta a rascunho; aprovação com senha e assinatura; quem elaborou ou enviou não aprova; aprovador sem perfil recusado; senha errada conta para o bloqueio da 005) (FR-002 a FR-009, FR-016, FR-017)
- [ ] T006 [US1] [US2] Implementar enviar, devolver, aprovar e descartar em `sgp/revisions/services.py`, retirar a publicação direta das telas e serviços públicos de `sgp/formtemplates` e `sgp/documents` e ajustar os testes das features 004 e 006 ao ciclo

## Phase 4: User Story 3 - Publicação e vigência (P1)

- [ ] T007 [P] [US3] Testes em `tests/revisions/test_validity.py` (vigência imediata: nova vigente e anterior substituída; vigência futura: novos documentos na anterior até a data, tarefa diária registra a entrada em vigência uma vez; documentos iniciados ficam na versão deles; publicado não muda; verificação de integridade íntegra e com adulteração no banco) (FR-010, FR-012 a FR-014, SC-002, SC-003)
- [ ] T008 [US3] Implementar a vigência, a tarefa `record_due` e a verificação em `sgp/revisions/services.py` e `tasks.py`

## Phase 5: User Story 4 - Histórico e comparação (P2)

- [ ] T009 [P] [US4] Testes em `tests/revisions/test_history.py` (histórico com etapas, pessoas, motivo, impacto e comentários; documentos iniciados por versão em formulário e layout; comparação entre duas versões quaisquer; trilha filtrada pelo modelo) (FR-016 a FR-019, SC-004)
- [ ] T010 [US4] Implementar as telas de revisões, histórico e comparação em `sgp/revisions/views.py` e templates, com os botões nas telas de modelos das features 004 e 006

## Phase 6: User Story 5 - Descarte e retirada de uso (P3)

- [ ] T011 [P] [US5] Testes em `tests/revisions/test_retirement.py` (descarte com motivo, consultável e libera nova revisão; retirada pedida com motivo, aprovada com assinatura ou devolvida com comentário; tipo retirado não aceita novo subdocumento; layout não é retirado) (FR-011, FR-015)
- [ ] T012 [US5] Implementar descarte e retirada em `sgp/revisions/services.py` e na regra de modelo vigente de `sgp/formtemplates/services.py`

## Phase 7: Polish

- [ ] T013 Permissões das rotas no contrato de `tests/core/test_route_scan.py` (FR-002, FR-004, SC-001)
- [ ] T014 [P] Atualizar `README.md` (feature 013) e registrar SC-005 como verificação manual
- [ ] T015 Rodar `scripts/verificar.sh` e corrigir o que faltar
- [ ] T016 Executar o quickstart na pilha real e registrar em `docs/validacao/013-resultados-execucao.md`

## Dependencies & Execution Order

Setup → Foundational → US1/US2 → US3 → US4 → US5 → Polish.

## Implementation Strategy

MVP = ciclo de revisão com aprovação assinada (US1 a US3); depois histórico, comparação, descarte e
retirada.
