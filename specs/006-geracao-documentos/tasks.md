---

description: "Task list for feature 006 — Geração de documentos no padrão da empresa"
---

# Tasks: Geração de documentos no padrão da empresa

**Input**: Design documents from `/specs/006-geracao-documentos/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, prova-layout/

**Tests**: obrigatórios (constituição VIII: TDD nas permissões, no determinismo, no selo e na adulteração, na marca d'água e na regressão visual); marcador `req("006:…")`.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

- [X] T001 Acrescentar `weasyprint`, `pyhanko` e `python-docx` (runtime) e `pypdfium2` e `pypdf` (desenvolvimento) em `pyproject.toml` e `uv.lock`; instalar `libpango-1.0-0`, `libpangoft2-1.0-0`, `libharfbuzz-subset0`, `fontconfig`, `fonts-crosextra-carlito` e `fonts-dejavu-core` no estágio `base` de `deploy/docker/Dockerfile`; criar a app `sgp/documents` (rotas `/documentos/` e `/modelos-layout/`, itens de navegação "Modelos de layout" e "Verificar documento"); `DOCUMENT_SEAL_PKCS12`, `DOCUMENT_SEAL_PASSWORD` e `DOCUMENT_GENERATION_TIME_LIMIT` (120 s) em `config/settings.py`, `.env.example` e `docker-compose.override.yml` (certificado de teste em `var/certs/`); faixa "Bioclin · Quibasa" em `sgp/documents/static/documents/logo-bioclin-quibasa.png`

## Phase 2: Foundational

- [X] T002 Implementar os modelos de data-model.md em `sgp/documents/models.py` e as migrações (gatilho de imutabilidade do layout publicado; `LayoutBinding`, `FrozenRendering` e `GeneratedDocument` somente de inclusão; restrição única parcial de pedido em andamento; migração de dados com a versão 01 publicada dos layouts `subdocument`, `charter` e `business_plan`), o tipo `docx` e `store_bytes` em `sgp/files/storage.py`, a política de acesso `generated_document` e os privilégios em `apply_db_privileges`
- [X] T003 [P] Escrever testes e implementar `sgp/documents/layout_schema.py` (padrões válidos; limites de margem, fonte, logotipo e cor; marcadores de cabeçalho e rodapé; códigos de tipo e variantes de capa) em `tests/documents/test_layout_schema.py` (FR-019, FR-022)
- [X] T004 [P] Escrever testes e implementar o vínculo de layout em `sgp/documents/layouts.py` (vigente por alvo e data; vínculo gravado no começo da versão; documento sem vínculo cai na primeira versão publicada; vínculo não muda com layout novo) em `tests/documents/test_layout_binding.py` (FR-021)
- [X] T005 Escrever testes e implementar o conteúdo de renderização de subdocumentos em `sgp/documents/content.py` conforme `contracts/conteudo-renderizacao.md` (capa, numeração de tópicos e tabelas da 004, não aplicável, valores formatados, referências na versão do cadastro, anexos com resumo, formulário opcional, variantes `checklist` e `sectors`, campos vazios) em `tests/documents/test_content.py` (FR-001, FR-004 a FR-010)
- [X] T006 [P] Registrar os eventos de `contracts/eventos-auditoria.md` em `sgp/documents/event_types.py` (FR-025; cada teste de fluxo confere o evento correspondente)

## Phase 3: User Stories 1, 2 e 3 - Gerar PDF e DOCX com capa e corpo no padrão (P1) 🎯 MVP

- [X] T007 [P] [US2] [US3] Testes em `tests/documents/test_render_pdf.py` (ordem e textos da capa; duas colunas na Entrada; Alteração com versões alterada e nova; CHECK LIST na capa da Verificação Final e ausente do corpo; setores da Saída com caixas; rótulo da Validação; títulos e tabelas numerados; tabela de 120 linhas com o cabeçalho em todas as páginas; "Página N de M"; marca d'água em todas as páginas do não aprovado; marcadores de PDF/A; mesmo conteúdo, mesmo arquivo) (FR-004 a FR-011, SC-002, SC-004)
- [X] T008 [US2] [US3] Implementar `sgp/documents/render_pdf.py` e `templates/documents/pdf/` (HTML e CSS a partir do layout; capa calibrada pela prova; identificador e datas fixos; imagens sem interpolação)
- [X] T009 [P] [US1] Testes em `tests/documents/test_render_docx.py` (A4 e margens do layout; cabeçalho e rodapé com PAGE e NUMPAGES; linha de cabeçalho repetida; marca d'água no não aprovado; "Cópia para conferência – o documento oficial é o PDF" no aprovado; DOCX normalizado igual em duas gerações) (FR-011, FR-015)
- [X] T010 [US1] Implementar `sgp/documents/render_docx.py`
- [X] T011 [P] [US1] Testes em `tests/documents/test_generation.py` (pedido na fila, gerando e concluído com arquivo arquivado e resumos; pedido em andamento reaproveitado; falha registrada sem arquivo; quem não vê o documento não gera nem baixa, inclusive pela URL; download confere integridade e registra; histórico de gerações; projeto cancelado continua gerando; o documento gerado registra a versão dos dados usada) (FR-001 a FR-003, FR-016, FR-018, FR-025)
- [X] T012 [US1] Implementar `sgp/documents/services.py`, `tasks.py`, as telas de documentos gerados, pedido (HTMX a cada 2 s) e download em `views.py`, `urls.py` e templates, e o link "Documentos gerados" no detalhe do subdocumento

## Phase 4: User Story 4 - PDF oficial com assinaturas, selo e código (P1)

- [X] T013 [P] [US4] Testes em `tests/documents/test_official.py` (só versão aprovada gera PDF oficial; selo íntegro e válido com o certificado de teste; 1 byte alterado acusado; sem certificado ou vencido, falha sem arquivo e com alerta; bloco da capa com "Elaborado" e "Aprovado", "Data:" da aprovação e delegação; relação final com "Revisado"; código igual nas regenerações; consulta do código com e sem acesso ao projeto, código inexistente e evento) (FR-012 a FR-015, SC-003)
- [X] T014 [US4] Implementar `sgp/documents/seal.py`, o comando `selo_teste`, o fluxo oficial em `services.py` e a tela de verificação do código

## Phase 5: User Story 6 - Conteúdo congelado e regeneração idêntica (P2)

- [X] T015 [P] [US6] Testes em `tests/documents/test_frozen.py` (aprovação congela o conteúdo na mesma transação com evento; regeneração com o mesmo resumo depois de renomear o produto em nova versão do TAP e o rótulo de um termo; divergência de conteúdo gera alerta; histórico indica igual à primeira; aprovação anterior à 006 congelada na primeira geração oficial) (FR-017, SC-005)
- [X] T016 [US6] Congelar o conteúdo em `sgp/signatures/services.py` (`approve`) chamando `sgp/documents/content.py`, e usar só o conteúdo congelado na geração de versão aprovada

## Phase 6: User Story 5 - Modelos de layout mantidos pela Qualidade (P2)

- [X] T017 [P] [US5] Testes em `tests/documents/test_layouts.py` (só Qualidade/AR cria, altera, pré-visualiza e publica; publicado não muda pelo serviço nem no banco; nova versão nasce do vigente; publicação recusada sem definição válida ou com vigência anterior à vigente; pré-visualização não arquiva; documento iniciado mantém o layout e o novo nasce no publicado; logotipo enviado com arquivo corrompido faz a geração falhar com a falha de integridade registrada) (FR-019 a FR-022, FR-025)
- [X] T018 [US5] Implementar os serviços de layout em `sgp/documents/layouts.py` e as telas de lista, detalhe, edição (formulário e logotipo), pré-visualização e publicação
- [X] T019 [US5] Vincular o layout no começo da versão: `sgp/subdocuments/services.py` (`create_subdocument`), `sgp/signatures/services.py` (`new_version`) e `sgp/projects/services.py` (criação do projeto)

## Phase 7: User Story 7 - TAP e Plano de Negócios (P3)

- [X] T020 [P] [US7] Testes em `tests/documents/test_project_documents.py` (TAP e Plano com capa, seções e tabelas numeradas, rodapé do layout vazio por padrão, oficial com selo e código; Plano exige permissão financeira para gerar, baixar e ver o projeto na consulta) (FR-023, FR-024)
- [X] T021 [US7] Implementar o conteúdo do TAP e do Plano em `sgp/documents/content.py` e o link "Documentos gerados" no detalhe do projeto

## Phase 8: Polish

- [X] T022 Regressão visual: `scripts/atualizar_referencias_visuais.sh`, referências em `tests/documents/referencias/` e `tests/documents/test_visual.py`; teste de desempenho de 30 páginas (SC-007, SC-008)
- [X] T023 Incluir as rotas no contrato de `tests/core/test_route_scan.py` e conferir as permissões de cada uma
- [X] T024 [P] Atualizar `README.md` (feature 006)
- [X] T025 Rodar `scripts/verificar.sh` e corrigir o que faltar
- [ ] T026 Executar o quickstart na pilha real (incluindo veraPDF e `pdfsig`), comparar a capa gerada com a da planilha e registrar em `docs/validacao/006-resultados-execucao.md`, com a comparação da Qualidade como pendência de ratificação (SC-001, SC-003, SC-006)

## Dependencies & Execution Order

Setup → Foundational (T002 antes de T003 a T006) → US1/US2/US3 (T007/T008 e T009/T010 antes de T011/T012) → US4 → US6 → US5 → US7 → Polish.

## Implementation Strategy

MVP = PDF e DOCX de rascunho dos subdocumentos com capa, corpo e marca d'água (US1 a US3); depois o
PDF oficial com selo e código, o congelamento, os modelos de layout pela tela e o TAP e o Plano.
