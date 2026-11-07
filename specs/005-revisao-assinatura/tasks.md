---

description: "Task list for feature 005 — Revisão, versões e assinatura eletrônica"
---

# Tasks: Revisão, versões e assinatura eletrônica

**Input**: Design documents from `/specs/005-revisao-assinatura/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: obrigatórios (constituição VIII: TDD na máquina de estados, na assinatura, na adulteração, na delegação e nas permissões); marcador `req("005:…")`.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

- [X] T001 Criar a app `sgp/signatures` (rotas `/assinaturas/`, item de navegação "Fila de revisão" para Gestor de P&D) com `SIGNATURE_MAX_FAILURES` (3), `SIGNATURE_LOCK_MINUTES` (15) e `REVIEW_ALERT_DAYS` (5) em `config/settings.py` e `.env.example`

## Phase 2: Foundational

- [X] T002 Implementar os modelos de data-model.md em `sgp/signatures/models.py` ("ApprovedVersion único por tipo, documento e versão"; `Signature`, `SignatureAttempt`, `ReviewComment` append-only com gatilhos; `SignatureLock`; `ApprovalDelegation`) e as migrações, incluindo `in_review`/`returned` em `Subdocument.status` e `doc_status`/`doc_version` em `ProjectCharter` e `BusinessPlan`
- [X] T003 [P] Escrever testes e implementar `sgp/signatures/canonical.py` (JSON canônico, SHA-256, estabilidade da ordem das chaves e decimais) em `tests/signatures/test_canonical.py` (FR-010)
- [X] T004 [P] Escrever testes e implementar `sgp/signatures/reauth.py` (senha certa, errada, AD indisponível sem contar falha, terceira falha seguida bloqueia com evento de alerta, expiração do bloqueio, senha nunca gravada) em `tests/signatures/test_reauth.py` (FR-006, FR-008, SC-004)
- [X] T005 Implementar os adaptadores de `sgp/signatures/documents.py` (subdocumento, TAP, Plano) conforme `contracts/conteudo-canonico.md` e os eventos de `contracts/eventos-auditoria.md` em `sgp/signatures/event_types.py`

## Phase 3: User Story 1 e 3 - Enviar e assinar (P1) 🎯 MVP

- [X] T006 [P] [US1] Testes em `tests/signatures/test_cycle.py` (envio exige completude e assinatura "elaborado"; em revisão não edita; assinatura guarda pessoa, função, significado, data e hora, versão e resumo; "revisado" por terceiro não muda a situação; elaborador e aprovador não assinam "revisado") (FR-002, FR-006, FR-009)
- [X] T007 [US1] Implementar `submit` e `sign_review` em `sgp/signatures/services.py`

## Phase 4: User Story 2 - Aprovar ou devolver (P1)

- [X] T008 [P] [US2] Testes em `tests/signatures/test_cycle.py` (devolução exige comentário e volta a editável; reenvio exige nova assinatura "elaborado" e a antiga não vale para o conteúdo novo; aprovação pelo Gestor com a senha congela a versão e bloqueia os cadastros; elaborador não aprova; Alteração aprovada sobe a versão do projeto) (FR-003, FR-004, FR-007, SC-002)
- [X] T009 [US2] Implementar `return_document` e `approve` em `sgp/signatures/services.py`, retirar a aprovação provisória pública de `sgp/subdocuments` e manter os efeitos da aprovação (bloqueio de cadastros, Alteração)

## Phase 5: User Story 4 - Versões (P1)

- [X] T010 [P] [US4] Testes em `tests/signatures/test_versions.py` (aprovado não edita; nova versão exige motivo, nasce em rascunho com o conteúdo aprovado; recusada com outra em andamento; versão anterior "Substituída" consultável com conteúdo e assinaturas) (FR-005, SC-003)
- [X] T011 [US4] Implementar `new_version` e a consulta de versões em `sgp/signatures/services.py`, `views.py` e `templates/signatures/version.html`

## Phase 6: User Story 5 - Integridade (P2)

- [X] T012 [P] [US5] Testes em `tests/signatures/test_integrity.py` (documento íntegro; conteúdo congelado alterado direto no banco apontado; conteúdo atual diferente do aprovado apontado; anexo alterado apontado; papel da aplicação sem UPDATE em versões e assinaturas; 10 versões em < 2 s) (FR-010, FR-011, SC-001, SC-005)
- [X] T013 [US5] Implementar `verify` em `sgp/signatures/services.py` com evento

## Phase 7: User Story 6 - Delegação e fila (P3)

- [X] T014 [P] [US6] Testes em `tests/signatures/test_delegation.py` (delegação com motivo, até 30 dias e perfil elegível; delegado aprova "em delegação de"; vencida ou encerrada recusada; delegado elaborador não aprova; fila mostra atrasados acima do prazo) (FR-013, FR-014)
- [X] T015 [US6] Implementar delegação e fila em `sgp/signatures/services.py`, `views.py` e templates

## Phase 8: TAP e Plano de Negócios (FR-012)

- [X] T016 [P] Testes em `tests/signatures/test_project_signatures.py` (submeter o projeto exige a senha do líder e assina TAP e Plano; aprovar exige a senha do Gestor e assina os dois; devolver devolve os dois; nova versão do TAP depois de aberto segue o ciclo) (FR-012)
- [X] T017 Integrar `sgp/projects/views.py`, `workflow.py`, `services.py` e templates com as assinaturas (senha nos formulários de submissão e aprovação; edição de TAP e Plano em nova versão)

## Phase 9: Polish

- [X] T018 Telas de envio, aprovação, devolução, revisão, nova versão e verificação em `sgp/signatures/views.py` e o bloco de assinaturas (rótulo da Validação) nos detalhes de subdocumento e de projeto (FR-015)
- [X] T019 Ajustar os testes e fixtures das features 002 e 004 ao ciclo com assinatura e incluir as rotas no contrato de `tests/core/test_route_scan.py`
- [X] T020 [P] Atualizar `README.md` (feature 005)
- [X] T021 Rodar `scripts/verificar.sh` e corrigir o que faltar
- [X] T022 Executar o quickstart na pilha real e registrar em `docs/validacao/005-resultados-execucao.md`

## Dependencies & Execution Order

Setup → Foundational → US1/US3 → US2 → US4 → US5 → US6 → TAP/Plano → Polish.

## Implementation Strategy

MVP = envio, assinatura e aprovação de subdocumentos (US1 a US3); depois versões, integridade,
delegação e o projeto.

---

## Phase 10: Convergence

- [X] T023 Recusar a aprovação por quem assinou "revisado" a mesma versão (separação dos papéis) em `sgp/signatures/services.py`, com teste em `tests/signatures/test_cycle_and_versions.py` per FR-009 (partial)
