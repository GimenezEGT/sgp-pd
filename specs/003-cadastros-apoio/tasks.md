---

description: "Task list for feature 003 — Cadastros de apoio"
---

# Tasks: Cadastros de apoio

**Input**: Design documents from `/specs/003-cadastros-apoio/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: obrigatórios (constituição VIII: TDD no versionamento, bloqueio, LGPD, importação, integridade de arquivos e permissões); marcador `req("003:…")`.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 Criar a app `sgp/files` (apps, `urls.py` em `/arquivos/`) e registrá-la em `config/settings.py` com `FILE_MAX_MB` (padrão 20) lido do ambiente; montar o volume nomeado `media` em `/app/var/media` para `web` e `worker` em `docker-compose.yml`
- [ ] T002 Criar a app `sgp/catalog` (apps, `urls.py` em `/cadastros/`, item de navegação "Cadastros" para todos os perfis em `sgp/core/navigation.py`) com a migração inicial que ativa a extensão `pg_trgm` (`TrigramExtension`) e a configuração `LOT_CODE_PATTERN` (padrão: "código alfanumérico que pode ter hífen, barra ou ponto, sem espaços") em `config/settings.py`
- [ ] T003 [P] Criar a migração de dados `sgp/vocab/migrations/0003_seed_amostras.py` com as listas `tipo-amostra` (Soro, Plasma, Sangue total, Urina, Líquor, DNA, RNA, Outros) e `armazenamento` (−20 °C, 2 a 8 °C, 2 a 30 °C, 15 a 30 °C, 37 °C) de data-model.md, reaproveitando `sgp/vocab/seed.py`, e o item de navegação "Listas controladas" só para Qualidade/AR

---

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T004 [P] Escrever testes que falham do armazenamento em `tests/files/test_storage.py`: SHA-256 calculado e caminho `aa/bb/<sha256>`; tipo conferido pela assinatura do arquivo e pela extensão (PDF `%PDF`, PNG, JPEG; CSV e XLSX só para importação); acima de `FILE_MAX_MB` recusado; leitura confere o SHA-256 e recusa arquivo alterado gravando `files.integrity_failed` com `{sha256 esperado}` → `{sha256 lido}` (FR-020, SC-005); papel da aplicação sem UPDATE em `StoredFile`
- [ ] T005 Implementar `StoredFile` *append-only* ("sha256 char(64), indexado", `original_name`, `content_type`, `size`, `storage_name` "caminho relativo aa/bb/<sha256>", `uploaded_by`, `uploaded_at`) com migração e gatilho de imutabilidade em `sgp/files/models.py`, e `store_upload`/`read_verified` em `sgp/files/storage.py` (gravação atômica, evento `files.uploaded` com `{nome, tipo, tamanho, sha256}`) e os tipos de evento em `sgp/files/event_types.py`
- [ ] T006 Implementar a rota `/arquivos/<id>/` em `sgp/files/views.py`: acesso decidido por políticas registradas pelas apps donas do arquivo (`sgp/files/access.py`, negação por padrão), leitura conferida e, na falha de integridade, evento gravado e página de erro sem desfazer a transação; testes em `tests/files/test_download.py`
- [ ] T007 Implementar `VersionedRecord` abstrato (`ProtectedModel`; `lineage` "UUID, indexado", `version` "inteiro ≥ 1, único por linhagem", `is_current` "uma única vigente por linhagem", `is_active`, `locked_at/locked_by/lock_reason`, `version_reason` "obrigatório a partir da versão 2", `row_version`, autor e datas) e os modelos `Lot`, `Material`, `ReferenceKit`, `Sample`, `Panel` (com `PanelSample` sem exclusão física), `Standard`, `BibliographicReference` e `ImportBatch` de data-model.md em `sgp/catalog/models.py`, com unicidade parcial entre vigentes, checagem "validade > fabricação", índices GIN `gin_trgm_ops` nos campos de busca e a migração
- [ ] T008 [P] Escrever testes que falham do versionamento em `tests/catalog/test_versioning.py`: correção no lugar com valor anterior e novo (FR-002); bloqueado sem motivo recusado e com motivo cria a versão 2 com a 1 intacta (FR-003, SC-001); código de lote e de insumo imutável depois de qualquer bloqueio da linhagem (FR-004); correção sem mudança não gera versão nem evento; histórico com todas as versões (FR-005); desativação e reativação com motivo (FR-006); papel da aplicação sem DELETE
- [ ] T009 Implementar `sgp/catalog/versioning.py` (`create_record`, `update_record` no lugar ou nova versão com `row_version`, `lock_version` com propagação do painel às amostras, `set_active`, `history`) e os eventos de `contracts/eventos-auditoria.md` em `sgp/catalog/event_types.py` (`object_id` = linhagem; `new_value` com `versao` e `registro`; lotes com `project_id`)
- [ ] T010 [P] Escrever testes e implementar `sgp/catalog/permissions.py` (editores = Analista/Pesquisador, Líder de projeto, Gestor de P&D e Qualidade/AR; lotes exigem acesso ao projeto pela regra única de `sgp.core.access`) em `tests/catalog/test_permissions.py` (FR-008, FR-009)
- [ ] T011 Implementar o registro de tipos `sgp/catalog/kinds.py` (slug da URL, modelo, formulário, rótulos, colunas da lista, campos de busca, campo de código congelado, se pertence a projeto) e as views genéricas de lista com busca e filtros, detalhe com versões e eventos, novo, editar, situação e busca em fragmento em `sgp/catalog/views.py`, `forms.py`, `urls.py` e `templates/catalog/`

**Checkpoint**: Foundation ready

---

## Phase 3: User Story 1 - Lotes do projeto (Priority: P1) 🎯 MVP

**Goal**: lotes por projeto com exibição padronizada e acesso pelo projeto.

**Independent Test**: cadastrar um lote num projeto aberto; validade anterior à fabricação recusada; pessoa sem acesso ao projeto barrada.

- [ ] T012 [P] [US1] Testes em `tests/catalog/test_lots.py` (FR-009 criação com evento e `project_id`, código repetido no mesmo projeto recusado e aceito em outro projeto, padrão `LOT_CODE_PATTERN`, validade anterior à fabricação recusada; FR-010 exibição "Lote <código> – Fabricação: MM/AAAA – Validade: MM/AAAA"; lista e busca só com lotes de projetos acessíveis; sem acesso ao projeto → 403 e `auth.permission_denied`)
- [ ] T013 [US1] Implementar `LotForm` (projetos acessíveis e abertos, responsável entre as pessoas ativas), `Lot.display` e as telas de lotes em `sgp/catalog/forms.py`, `models.py` e `templates/catalog/`

---

## Phase 4: User Story 2 - Versões e bloqueio (Priority: P1)

**Goal**: correção no lugar até o bloqueio; depois, nova versão com motivo.

**Independent Test**: bloquear um lote, corrigir a validade pela tela e conferir versão 2, versão 1 intacta e referência antiga com o valor original.

- [ ] T014 [P] [US2] Testes de ponta a ponta pelas telas em `tests/catalog/test_lock_flow.py` (motivo exigido só quando bloqueado; versão 2 criada; detalhe da versão 1 mostra o valor original e indica a versão vigente; mudança de código bloqueada recusada; histórico com autor, data e motivo; edição de versão substituída leva à vigente; conflito de edição simultânea)
- [ ] T015 [US2] Implementar no formulário de edição o campo de motivo e as mensagens de bloqueio, e no detalhe o quadro de versões e os eventos da trilha da linhagem em `sgp/catalog/views.py` e `templates/catalog/detail.html`

---

## Phase 5: User Story 3 - Insumos e importação (Priority: P1)

**Goal**: insumos com certificado conferido e importação com pré-visualização.

**Independent Test**: importar 500 linhas com inválidas, confirmar e baixar o relatório de rejeições.

- [ ] T016 [P] [US3] Testes em `tests/catalog/test_materials.py` (FR-011 código único entre vigentes; certificado PDF anexado com evento `files.uploaded`; validade do certificado exigida quando há certificado; FR-012 alerta "Certificado vencido" no detalhe e na busca sem bloquear; download do certificado conferido)
- [ ] T017 [P] [US3] Testes em `tests/catalog/test_importing.py` (FR-013: CSV `;` e `,`, UTF-8 com e sem BOM, Latin-1, XLSX; coluna obrigatória faltando recusa o arquivo com as colunas esperadas; código repetido na planilha rejeita a segunda linha; código existente rejeitado sem alterar o insumo; sinônimos de `tipo` e `novo`; pré-visualização não cria insumo; confirmação cria só as válidas e revalida o código; relatório `linha;codigo;descricao;motivos` em UTF-8 com BOM; limite de 5.000 linhas; pré-visualização abandonada fica não confirmada; SC-002 500 linhas em < 30 s)
- [ ] T018 [US3] Implementar `sgp/catalog/importing.py` (leitura, normalização do cabeçalho sem acento e sem caixa, validação linha a linha, pré-visualização, confirmação, relatório de rejeições e planilha modelo) conforme `contracts/importacao-insumos.md`
- [ ] T019 [US3] Implementar `MaterialForm` com anexo do certificado, as telas de importação (`/cadastros/insumos/importar/`, `<lote>/`, `rejeicoes.csv`, `modelo.csv`) e a política de acesso dos arquivos do catálogo em `sgp/catalog/views.py`, `forms.py`, `files_access.py` e `templates/catalog/`

---

## Phase 6: User Story 4 - Kits, amostras e painéis (Priority: P2)

**Goal**: base dos estudos sem dados pessoais de pacientes.

**Independent Test**: cadastrar kit, amostras e painel; tentar nome, CPF, e-mail e telefone em campos de amostra.

- [ ] T020 [P] [US4] Testes em `tests/catalog/test_lgpd.py` (FR-015 identificador `^[A-Za-z0-9][A-Za-z0-9._/-]{0,29}$` com ao menos um dígito; FR-016 CPF com e sem pontuação, e-mail, telefone e as palavras "paciente" e "nome" recusados em origem, caracterização e detalhe do armazenamento; SC-003)
- [ ] T021 [P] [US4] Testes em `tests/catalog/test_kits_samples_panels.py` (FR-014 exibição do kit; FR-017 painel referencia versões de amostras, uma amostra em vários painéis, uma só versão por amostra no painel; nova versão da amostra mantém o painel na versão antiga; bloquear painel bloqueia as amostras; amostra desativada aparece no painel com a indicação; termos desativados fora dos novos cadastros e mantidos nos antigos)
- [ ] T022 [US4] Implementar `sgp/catalog/lgpd.py` e os formulários e telas de kits, amostras (listas controladas ativas mais o termo já usado) e painéis (amostras vigentes e ativas mais as já referenciadas) em `sgp/catalog/forms.py` e `templates/catalog/`

---

## Phase 7: User Story 5 - Bibliotecas e listas controladas (Priority: P2)

**Goal**: normas e referências reutilizáveis e listas mantidas pela Qualidade.

**Independent Test**: cadastrar norma e referência e achá-las na busca; como Qualidade, incluir e desativar termos conferindo versão e trilha.

- [ ] T023 [P] [US5] Testes em `tests/catalog/test_libraries.py` (FR-018 identificação de norma única entre vigentes e abrangência; referência com ano e DOI opcionais; FR-007 busca por trecho de código ou descrição, só ativos e vigentes, até 20 resultados; SC-004 busca em < 1 s com 10 mil insumos)
- [ ] T024 [P] [US5] Testes em `tests/vocab/test_vocab_admin.py` (FR-019 Qualidade inclui termo com código gerado, corrige rótulo, desativa e reativa com motivo; cada mudança sobe a versão da lista e grava `vocab.*`; outro perfil recebe 403 e o evento de negação)
- [ ] T025 [US5] Implementar `sgp/vocab/services.py`, `forms.py`, `views.py`, `urls.py` (`/listas/`) e `templates/vocab/` e os tipos de evento `vocab.*` em `sgp/vocab/event_types.py`

---

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T026 Incluir as rotas de `contracts/rotas-ui.md` no contrato de `tests/core/test_route_scan.py` (perfis exigidos, acesso por projeto e política de arquivos)
- [ ] T027 [P] Documentar os cadastros, a importação e as listas controladas no `README.md` e as variáveis novas no `.env.example`
- [ ] T028 Rodar `scripts/verificar.sh` (ruff, testes, cobertura, matriz) e corrigir o que faltar
- [ ] T029 Executar o quickstart na pilha real (curl) e registrar em `docs/validacao/003-resultados-execucao.md`

---

## Dependencies & Execution Order

- Setup → Foundational → US1 → US2 → US3 → US4 → US5 → Polish (um desenvolvedor, em ordem de prioridade).
- T005 antes de T006 e T019 (arquivos); T007 antes de T009 e das histórias; T009 antes de T011.
- US2 usa os lotes da US1 como exemplo; US3, US4 e US5 dependem só da fundação.

## Parallel Example: User Story 3

```bash
Task: "Testes em tests/catalog/test_materials.py"
Task: "Testes em tests/catalog/test_importing.py"
```

## Implementation Strategy

MVP = US1 e US2 (lotes versionados com bloqueio); US3 entrega insumos e importação; US4 e US5 completam a base dos estudos e as listas.

## Notes

- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each logical group
