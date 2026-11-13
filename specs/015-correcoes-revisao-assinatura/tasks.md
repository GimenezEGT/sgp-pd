---

description: "Task list for feature 015 — Correções do ciclo de revisão e assinatura"
---

# Tasks: Correções do ciclo de revisão e assinatura

**Input**: Design documents from `/specs/015-correcoes-revisao-assinatura/`

**Tests**: obrigatórios (constituição VIII); marcador `req("015:…")`; fixtures da feature 005.

## Phase 1: Setup

- [ ] T001 `STATUS_LABELS` (Rascunho, Em revisão, Devolvido, Aprovado) em `sgp/signatures/documents.py`

## Phase 2: User Story 2 - Assinatura "Revisado" uma vez por versão (P1)

**Goal**: a mesma pessoa assina "Revisado" uma vez por versão.

**Independent Test**: assinar, conferir a opção oculta e a recusa da segunda tentativa; nova versão permite revisar de novo.

- [ ] T002 [P] [US2] Testes em `tests/signatures/test_correcoes_015.py`: segunda assinatura "Revisado" da mesma pessoa na mesma versão recusada com "Você já assinou como revisor esta versão." e sem gravar; `can_review` falso para quem já revisou; nova versão em revisão permite revisar (FR-005, SC-001)
- [ ] T003 [US2] Implementar a recusa em `sign_review` e a condição de `can_review` em `block_context`, em `sgp/signatures/services.py`

## Phase 3: User Story 1 - Gestor que elaborou entende e destrava o documento (P1) 🎯 MVP

**Goal**: aviso, devolução, seção própria na fila e aviso no envio para o Gestor que elaborou.

**Independent Test**: enviar como Gestor e conferir o bloco de assinaturas, a fila e a tela de aprovação.

- [ ] T004 [P] [US1] Testes em `tests/signatures/test_correcoes_015.py`: Gestor que elaborou vê o aviso, o link para Delegações e o formulário "Devolver" na tela do documento e devolve com comentário (situação Devolvido, evento `signatures.returned`); devolução sem comentário recusada; analista que elaborou não vê a devolução; Fila de revisão com a seção "Elaborados por você" (sem link de aprovação) e sem o documento na lista aprovável; tela de envio avisa o Gestor e não avisa a analista; tela de aprovação sem "Aprovar e assinar" para quem elaborou e aprovação pelo endereço direto recusada (FR-001 a FR-004, FR-007, SC-002)
- [ ] T005 [US1] Implementar `own_submission` e `can_return_own` em `block_context` e `review_queue(user, own=True)` em `sgp/signatures/services.py`; aviso e devolução em `sgp/signatures/templates/signatures/_block.html`; seção própria em `queue.html` e `queue_view` em `sgp/signatures/views.py`; avisos do envio e da aprovação em `sign.html` e no contexto de `submit_view`/`approve_view`

## Phase 4: User Story 3 - Situação pelo nome (P2)

- [ ] T006 [US3] Testes e implementação de `status_label` no contexto das telas de envio e aprovação (`sgp/signatures/views.py`, `sign.html`): "Em revisão" na tela e nenhum código interno (FR-006, SC-003)

## Phase 5: Polish

- [ ] T007 `README.md` (linha da feature 015); rotas sem mudança no contrato de `tests/core/test_route_scan.py`
- [ ] T008 Rodar `scripts/verificar.sh`
- [ ] T009 Executar o quickstart na pilha real (Entrada do PD-2026-003) e registrar em `docs/validacao/015-resultados-execucao.md`

## Dependencies & Execution Order

Setup → US2 → US1 → US3 → Polish (todas na mesma app; US2 e US1 tocam `services.py` em sequência).

## Implementation Strategy

US2 e US1 juntas destravam o problema do teste do usuário; US3 é polimento de tela.
