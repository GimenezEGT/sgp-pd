---

description: "Task list for feature 011 — Dossiê técnico para a ANVISA"
---

# Tasks: Dossiê técnico para a ANVISA

**Input**: Design documents from `/specs/011-dossie-tecnico/`

**Tests**: obrigatórios (constituição VIII); marcador `req("011:…")`; dados fictícios criados nos testes.

## Phase 1: Setup

- [ ] T001 Acrescentar PyYAML em `pyproject.toml` e `uv.lock`; criar a app `sgp/dossier` com a definição padrão `definicao_padrao.yaml` (estrutura I a XII do contexto), o ZIP gerado em `sgp/files/storage.py` e os itens do menu

## Phase 2: Foundational

- [ ] T002 [P] Testes e implementação de `definition.py` (validação do YAML: numeração, classes, tipos de fonte) em `tests/dossier/test_definition.py` (FR-002)
- [ ] T003 Implementar os modelos com migração (definição semeada), gatilhos de imutabilidade e eventos

## Phase 3: User Story 1 - Checagem (P1) 🎯 MVP

- [ ] T004 [P] Testes em `tests/dossier/test_check.py` (classe da Entrada; itens por classe; origem e status; não aplicável com justificativa da origem ou do complemento; sem justificativa conta como faltando; fora da classe com a justificativa da definição; família) (FR-001, FR-003, FR-009)
- [ ] T005 Implementar `sources.py` e `check.py`

## Phase 4: User Stories 2 e 4 - Geração e declaração (P1)

- [ ] T006 [P] Testes em `tests/dossier/test_generation.py` (árvore de títulos I a XII no PDF e no DOCX; cabeçalho e rodapé; nome do produto em itálico; tabelas numeradas; rascunho com item faltando; final com pacote ZIP de anexos; declaração do RT/RL; arquivado com resumo; permissões) (FR-004 a FR-007, FR-010, FR-013, SC-001, SC-003)
- [ ] T007 Implementar `render.py`, a geração em `services.py` e as telas

## Phase 5: User Stories 3, 5 e 6 - Textos, aditamento e envio (P2)

- [ ] T008 Testes e implementação da biblioteca de textos (versões, aprovação com senha por outra pessoa), do registro de envio e resultado (classe I sem envio) e do aditamento (só os itens que mudaram) em `tests/dossier/test_texts_submissions.py` (FR-008, FR-011, FR-012, SC-002)

## Phase 6: Polish

- [ ] T009 Rotas no contrato de `tests/core/test_route_scan.py`; `README.md` (feature 011); SC-004 em `docs/validacao/verificacoes-manuais.json`
- [ ] T010 Rodar `scripts/verificar.sh`
- [ ] T011 Executar o quickstart na pilha real e registrar em `docs/validacao/011-resultados-execucao.md`

## Dependencies & Execution Order

Setup → Foundational → US1 → US2/US4 → US3/US5/US6 → Polish.
