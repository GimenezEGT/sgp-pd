---

description: "Task list for feature 012 — Integração com o Sankhya"
---

# Tasks: Integração com o Sankhya

**Input**: Design documents from `/specs/012-integracao-sankhya/`

**Tests**: obrigatórios (constituição VIII); marcador `req("012:…")`; servidor HTTP simulado; dados fictícios.

## Phase 1: Setup

- [X] T001 Criar a app `sgp/integrations` com as variáveis `SANKHYA_*` (`.env.example`, `config/settings.py`), a varredura no beat, o mapeamento padrão e os itens do menu

## Phase 2: Foundational

- [X] T002 [P] Servidor simulado do gateway em `tests/integrations/conftest.py`; testes e implementação de `sankhya.py` e `payloads.py` (token, renovação depois de 401, X-Token, loadRecords, saveRecord, erro do gateway) em `tests/integrations/test_client.py` (FR-001, FR-002)
- [X] T003 Implementar `IntegrationMapping` e `IntegrationMessage` com migração (mapeamento semeado), eventos e `mapping.py`

## Phase 3: User Stories 2 e 4 - Outbox, envio e fila (P1) 🎯 MVP

- [X] T004 [P] Testes em `tests/integrations/test_outbox.py` (mensagem na transação da aprovação; registros do contrato; envio único com reenvio; aguardando configuração; falha com espera crescente; reprocessamento; aprovação continua com o ERP fora do ar; fila só para a TI) (FR-004, FR-005, FR-007, FR-009, SC-001, SC-004)
- [X] T005 Implementar `records.py`, `services.py`, `signals.py`, `tasks.py` e a fila

## Phase 4: User Stories 1, 3 e 5 - Consulta, insumos novos e contingência (P1/P2)

- [X] T006 Testes e implementação da consulta de produto (com e sem ERP), das solicitações de insumo novo da Saída e da exportação CSV, XLSX e JSON em `tests/integrations/test_lookup_export.py` (FR-003, FR-006, FR-008, SC-003)

## Phase 5: Polish

- [X] T007 Rotas no contrato de `tests/core/test_route_scan.py`; `README.md` (feature 012); SC-002 em `docs/validacao/verificacoes-manuais.json`
- [X] T008 Rodar `scripts/verificar.sh` (1204 testes, cobertura mínima e matriz com 290 requisitos cobertos)
- [X] T009 Executar o quickstart na pilha real e registrar em `docs/validacao/012-resultados-execucao.md`

## Dependencies & Execution Order

Setup → Foundational → US2/US4 → US1/US3/US5 → Polish.

## Phase 6: Convergence

- [X] T010 Atualizar o registro "documento" no Sankhya (mesma chave do registro, sem duplicar) quando o primeiro PDF oficial da versão aprovada for gerado, com `pdf_sha256` e `pdf_codigo_verificacao`, em `sgp/integrations/` com teste per FR-004 (partial)
- [X] T011 Escrever limites e valores dos critérios do registro "resultado_estudo" com vírgula decimal, como na tela do estudo, em `sgp/integrations/records.py` com teste per FR-008 (partial)
- [X] T012 Testar o registro "lote" gerado por lote citado em subdocumento aprovado em `tests/integrations/` per contrato registros.md (partial)
