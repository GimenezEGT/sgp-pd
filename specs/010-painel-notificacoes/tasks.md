---

description: "Task list for feature 010 — Painel do gestor e notificações"
---

# Tasks: Painel do gestor e notificações

**Input**: Design documents from `/specs/010-painel-notificacoes/`

**Tests**: obrigatórios (constituição VIII); marcador `req("010:…")`; dados fictícios criados nos testes.

## Phase 1: Setup

- [X] T001 Criar as apps `sgp/dashboard` e `sgp/notifications`, as configurações de e-mail, cache e resumo diário (`.env.example`, `config/settings.py`, beat), o e-mail em arquivo no desenvolvimento e os itens do menu

## Phase 2: Foundational

- [X] T002 Implementar `NotificationPreference` e `Notification` com migração, os índices dedicados e os eventos

## Phase 3: User Stories 1 e 3 - Carteira e fila do gestor (P1) 🎯 MVP

- [X] T003 [P] Testes em `tests/dashboard/test_portfolio.py` (etapa atual, percentual, marcos, atraso, líder; quatro totais; regra única de acesso; custo e retorno só com permissão; cache; 100 projetos em < 2 s) (FR-001, FR-002, FR-004, SC-001, SC-003)
- [X] T004 Implementar `portfolio.py`, a tela do painel com SVG e o vínculo para a fila da 005

## Phase 4: User Story 4 - Pendências e e-mails (P1)

- [X] T005 [P] Testes em `tests/notifications/test_notifications.py` (devolução e aprovação imediatas com destinatários; preferência desligada omite; assinatura pendente não desliga; resumo diário no dia seguinte ao prazo com chave por dia; sem e-mail omitida; falha com novas tentativas; eventos) (FR-007 a FR-009, SC-002)
- [X] T006 Implementar `sgp/notifications` (sinal da trilha, destinatários, envio, resumo diário, preferências) e "Minhas pendências" em `sgp/dashboard/pending.py` (FR-005)

## Phase 5: User Stories 2 e 5 - Linha do tempo e exportação (P2)

- [X] T007 Testes e implementação da linha do tempo (ordem, categorias, acesso, sem valores) e da exportação XLSX (colunas, permissões, evento) em `tests/dashboard/test_timeline_export.py` (FR-003, FR-006)

## Phase 6: Polish

- [X] T008 Rotas no contrato de `tests/core/test_route_scan.py`; `README.md` (feature 010)
- [X] T009 Rodar `scripts/verificar.sh`
- [X] T010 Executar o quickstart na pilha real e registrar em `docs/validacao/010-resultados-execucao.md`

## Dependencies & Execution Order

Setup → Foundational → US1/US3 → US4 → US2/US5 → Polish.
