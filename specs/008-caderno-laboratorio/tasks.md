---

description: "Task list for feature 008 — Caderno de laboratório eletrônico"
---

# Tasks: Caderno de laboratório eletrônico

**Input**: Design documents from `/specs/008-caderno-laboratorio/`

**Tests**: obrigatórios (constituição VIII); marcador `req("008:…")`; dados fictícios criados nos testes.

## Phase 1: Setup

- [X] T001 Acrescentar `nh3` (runtime) em `pyproject.toml` e `uv.lock`; criar a app `sgp/notebook` com as rotas `/caderno/` e `/projetos/<id>/caderno/`, `NOTEBOOK_SIGN_DAYS` em `config/settings.py` e o item "Caderno" no menu

## Phase 2: Foundational

- [X] T002 [P] Escrever testes e implementar `sgp/notebook/richtext.py` conforme `contracts/conteudo-assinado.md` (lista branca, imagem só de anexo da entrada, texto simples em parágrafos e listas, texto puro sem acentos) em `tests/notebook/test_richtext.py` (FR-001, FR-003)
- [X] T003 Implementar os modelos, a migração com o `tsvector` gerado e os índices GIN, os gatilhos de bloqueio e de imutabilidade, os eventos e a política de leitura de arquivo em `sgp/notebook`

## Phase 3: User Stories 1 e 3 - Entrada, assinatura e adendos (P1) 🎯 MVP

- [X] T004 [P] Testes em `tests/notebook/test_entries.py` (número e hora do servidor; editores do projeto criam, só o autor edita; materiais pela versão do cadastro e código inexistente recusado; anexos nos tipos e no limite, resumo conferido na leitura; acesso ao arquivo só para quem acessa o projeto; negação registrada) (FR-001 a FR-004, FR-014)
- [X] T005 [P] Testes em `tests/notebook/test_signing.py` (assinatura com reautenticação e bloqueio da 005; resumo canônico; entrada assinada recusa edição, material e anexo no serviço e no banco; adendo assinado e imutável sem mudar o original; atrasada depois do prazo) (FR-006 a FR-008, SC-001)
- [X] T006 Implementar `sgp/notebook/permissions.py`, `content.py`, `services.py` e as telas de nova entrada, detalhe, edição (com `static/notebook/editor.js`), materiais, anexos, assinatura e adendo

## Phase 4: User Story 4 - Testemunha (P2)

- [X] T007 Testes e implementação da relevância (autor ou Gestor de P&D, até haver testemunha) e do testemunho (acesso ao projeto, diferente do autor, resumo conferido; aguardando testemunha) em `tests/notebook/test_signing.py` (FR-009)

## Phase 5: User Story 2 - Modelos de entrada (P2)

- [X] T008 Testes e implementação dos modelos de entrada (Qualidade/AR e Gestor de P&D; nova versão com motivo; desativar; a entrada copia os textos e guarda a versão; entrada antiga não muda) em `tests/notebook/test_templates.py` (FR-005)

## Phase 6: User Story 5 - Vínculos e promoção (P2)

- [X] T009 [P] Testes em `tests/notebook/test_links.py` (subdocumento, lote e estudo do mesmo projeto; outro projeto recusado; retirada lógica com motivo; vínculo com entrada assinada; exibição no subdocumento, no estudo e no lote; promoção de CSV e XLSX para estudo em elaboração com vínculo nos dois sentidos; estudo bloqueado recusado) (FR-010, FR-011, SC-003)
- [X] T010 Implementar vínculos, `sgp/notebook/promotion.py`, a tela de promoção e os trechos de template em subdocumento, estudo e lote

## Phase 7: User Story 6 - Linha do tempo e busca (P2)

- [X] T011 [P] Testes em `tests/notebook/test_search.py` (linha do tempo paginada por data; busca em português com e sem acento, em entrada e adendo; lote em materiais e vínculos; amostra; pesquisador; período; situação e aberta há mais de N dias; só projetos acessíveis; 1.000 entradas em < 2 s) (FR-012, FR-013, SC-002, SC-004)
- [X] T012 Implementar `sgp/notebook/search.py` e as telas `/caderno/` e `/projetos/<id>/caderno/` com "carregar mais" por HTMX

## Phase 8: Polish

- [X] T013 Rotas no contrato de `tests/core/test_route_scan.py`; `README.md` (feature 008)
- [X] T014 Rodar `scripts/verificar.sh`
- [X] T015 Executar o quickstart na pilha real e registrar em `docs/validacao/008-resultados-execucao.md`

## Dependencies & Execution Order

Setup → Foundational → US1/US3 → US4 → US2 → US5 → US6 → Polish. US2 vem depois do MVP porque a
entrada funciona sem modelo; US5 depende da 007 (importação) e das entradas; US6 depende dos
materiais e vínculos.
