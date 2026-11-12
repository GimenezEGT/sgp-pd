---

description: "Task list for feature 009 — Documento completo do projeto"
---

# Tasks: Documento completo do projeto

**Input**: Design documents from `/specs/009-documento-completo/`

**Tests**: obrigatórios (constituição VIII); marcador `req("009:…")`; dados fictícios criados nos testes.

## Phase 1: Setup

- [ ] T001 Criar a app `sgp/fulldoc` (rotas `/projetos/<id>/documento-completo/` e `/documentos-completos/`), extrair a capa e os tópicos do template da 006 para `_cover.html` e `_sections.html` sem mudar os PDFs da 006

## Phase 2: Foundational

- [ ] T002 Implementar `FullDocumentRequest` e `FullDocument` com migração, gatilho de imutabilidade, eventos e o registro de consultas extras na verificação da 006

## Phase 3: User Stories 1 e 5 - Gerar com um clique e pendências (P1) 🎯 MVP

- [ ] T003 [P] Testes em `tests/fulldoc/test_pending.py` (tipos do fluxo sem versão aprovada; subdocumento sem versão aprovada; versão sem conteúdo congelado; itens da Verificação Final com disposição diferente de Aprovado; projeto completo sem pendências) (FR-012)
- [ ] T004 [P] Testes em `tests/fulldoc/test_generation.py` (ordem das partes do contrato; sumário com as páginas reais; numeração "Página X de Y"; rascunho com marca d'água e pendências; oficial com selo, PDF/A e código de verificação reconhecido na verificação; arquivado com SHA-256; reaproveitamento sem mudanças; falha registrada; quem gera e quem baixa; negação registrada) (FR-001 a FR-006, FR-013 a FR-015, SC-001, SC-002)
- [ ] T005 Implementar `pending.py`, `compose.py`, `render.py`, `services.py`, `tasks.py` e as telas (pendências, opções, progresso por HTMX, histórico e download)

## Phase 4: User Story 3 - Quadro de versões e resumo da trilha (P1)

- [ ] T006 Testes e implementação do quadro de versões (todas as versões aprovadas, signatários) e do resumo da trilha (período, por tipo, eventos-chave) em `tests/fulldoc/test_content.py` (FR-008, FR-009)

## Phase 5: User Stories 2 e 4 - Caderno e histórico de versões (P2)

- [ ] T007 Testes e implementação do caderno completo ou resumido (só entradas assinadas; imagens embutidas; vínculos), do histórico completo de versões (substituídas marcadas), do Plano de Negócios sem dados financeiros e da lista de anexos em `tests/fulldoc/test_content.py` (FR-005, FR-007, FR-010, FR-011)

## Phase 6: Polish

- [ ] T008 Teste de desempenho de 300 páginas (`slow`) em `tests/fulldoc/test_performance.py` (SC-003); SC-004 em `docs/validacao/verificacoes-manuais.json`
- [ ] T009 Rotas no contrato de `tests/core/test_route_scan.py`; `README.md` (feature 009)
- [ ] T010 Rodar `scripts/verificar.sh` e `pytest -m slow tests/fulldoc`
- [ ] T011 Executar o quickstart na pilha real e registrar em `docs/validacao/009-resultados-execucao.md`

## Dependencies & Execution Order

Setup → Foundational → US1/US5 → US3 → US2/US4 → Polish.
