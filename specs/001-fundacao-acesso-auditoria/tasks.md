---

description: "Task list for feature 001 — Fundação: acesso, perfis e trilha de auditoria"
---

# Tasks: Fundação — acesso, perfis e trilha de auditoria

**Input**: Design documents from `/specs/001-fundacao-acesso-auditoria/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: obrigatórios. A constituição (princípio VIII) exige TDD para regras regulatórias,
cálculos e permissões; cada teste leva `@pytest.mark.req("001:FR-xxx")` ou `("001:SC-xxx")`.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Monólito Django: código em `config/` e `sgp/<app>/`, testes em `tests/<app>/`, implantação em
`deploy/`. Comandos de teste rodam no contêiner: `docker compose run --rm web pytest`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Criar `pyproject.toml` (projeto `sgp-pd`, Python `>=3.12,<3.13`) com Django `==5.2.19`, django-auth-ldap `5.4`, python-ldap `3.4.8`, psycopg[binary] `3.3`, celery[redis] `5.7`, gunicorn, whitenoise, openpyxl `3.1.5`; grupo dev com pytest `9`, pytest-django `4.14`, pytest-cov `7`, ruff; configurar `[tool.pytest.ini_options]` (`DJANGO_SETTINGS_MODULE=config.settings_test`, marcadores `req`, `ldap`, `slow`, cobertura de `sgp.core` e `sgp.audit` com `--cov-fail-under=90`) e `[tool.ruff]`; gerar `uv.lock`
- [ ] T002 Criar o projeto Django em `manage.py` e `config/` (`settings.py` lendo variáveis de ambiente de `contracts/configuracao.md`, `LANGUAGE_CODE="pt-br"`, `TIME_ZONE="America/Sao_Paulo"`, `USE_TZ=True`, sem `django.contrib.admin`; `settings_test.py` com credenciais do papel dono e backend de autenticação falso; `urls.py`; `wsgi.py`; `celery.py`)
- [ ] T003 [P] Criar `deploy/docker/Dockerfile` (estágios `builder` com libldap2-dev/libsasl2-dev e uv, `runtime` sem ferramentas de build e usuário não root, `dev` com dependências de teste) e `deploy/docker/entrypoint.sh` (aguarda o banco, `migrate` com `DB_OWNER_*`, `apply_db_privileges`, inicia o processo com `DB_USER`)
- [ ] T004 [P] Criar `deploy/postgres/initdb/01-papeis.sh` que cria o papel `sgp_app` (LOGIN, senha de `APP_DB_PASSWORD`, sem privilégios iniciais)
- [ ] T005 [P] Criar `deploy/nginx/Dockerfile`, `deploy/nginx/nginx.conf` (HTTPS só, redireciono de HTTP, cabeçalhos HSTS, CSP `default-src 'self'`, `X-Frame-Options DENY`, proxy para `web:8000`) e `deploy/nginx/10-certificado-dev.sh` (gera certificado autoassinado em `/etc/nginx/certs` se ausente)
- [ ] T006 [P] Criar `deploy/ldap-dev/seed.ldif` com os usuários fictícios do quickstart (senha `Senha#Dev01`; `ex.colaborador` sem senha) e grupos `sgp-administradores`, `sgp-gestores`, `sgp-analistas`, `sgp-qualidade`
- [ ] T007 Criar `docker-compose.yml` (db postgres:17-bookworm, redis:7.4-alpine, web, worker `celery -A config worker --beat`, nginx; healthchecks; volume `pgdata`), `docker-compose.override.yml` (ldap osixia/openldap:1.5.0 com `ulimits.nofile=1024`, código montado em `/app`, `runserver`, alvo `dev`) e `.env.example`; criar `.dockerignore`
- [ ] T008 [P] Baixar HTMX 2.0.11 do registro npm para `sgp/core/static/core/vendor/htmx.min.js` com a licença em `sgp/core/static/core/vendor/HTMX-LICENSE`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T009 Criar `tests/conftest.py` com o plugin de rastreabilidade (opção `--req-report=<arquivo>` que grava JSON teste → requisitos), fixtures de pessoas com perfis, `auth_client(perfis)` e o backend falso `tests/fake_backend.py` (credenciais por dicionário, grupos de rede simulados, simulação de indisponibilidade)
- [ ] T010 [P] Escrever testes que falham para modelos protegidos em `tests/core/test_protected_models.py` (FR-026: `delete()` e `QuerySet.delete()` recusados; append-only recusa `save()` de registro existente)
- [ ] T011 Implementar `ProtectedModel`, `AppendOnlyModel` e `ProtectedQuerySet` em `sgp/core/models.py`
- [ ] T012 Implementar `accounts.User` em `sgp/accounts/models.py` com os campos de data-model.md ("username varchar(150), único — login de rede normalizado em minúsculas"; "password sempre inutilizável"; `full_name`, `first_name`, `last_name`, `email`, `job_title`, `is_active`, `created_at`, `last_login`) e gerenciador; `AUTH_USER_MODEL="accounts.User"`; migração `sgp/accounts/migrations/0001_initial.py`
- [ ] T013 Implementar `ProfileAssignment` em `sgp/accounts/models.py` ("profile varchar(20): ADMIN, RD_MANAGER, PROJECT_LEADER, ANALYST, QUALITY, READER"; "source manual ou network_group"; "índice único parcial (user, profile) WHERE revoked_at IS NULL"; motivo obrigatório) com migração
- [ ] T014 [P] Escrever testes que falham da serialização canônica e do hash em `tests/audit/test_chain.py` (FR-020: chaves ordenadas, UTC com microssegundos, genesis com 64 zeros, valores sem ponto flutuante, hash estável após ida e volta pelo banco)
- [ ] T015 Implementar `sgp/audit/chain.py` (`to_jsonable`, `canonical_payload`, `compute_hash`, `GENESIS_HASH`)
- [ ] T016 Implementar `AuditEvent` e `ChainVerification` em `sgp/audit/models.py` conforme data-model.md ("seq bigint PK 1, 2, 3… sem lacunas"; "hash char(64), único"; índices de consulta) e migração com o trigger `audit_event_immutable` (BEFORE UPDATE OR DELETE, também em `audit_chainverification`)
- [ ] T017 [P] Implementar o catálogo de eventos em `sgp/audit/event_types.py` (códigos e rótulos de `contracts/eventos-auditoria.md`, registro extensível pelas outras apps)
- [ ] T018 Escrever testes que falham de `record_event` em `tests/audit/test_record_event.py` (FR-018, FR-020: sequência sem lacunas, encadeamento, autor "sistema", rollback desfaz evento e mudança, gravação concorrente em duas threads sem bifurcação)
- [ ] T019 Implementar `record_event` com `pg_advisory_xact_lock` e captura da origem da requisição em `sgp/audit/services.py` e `sgp/core/request_context.py` (middleware que guarda IP e usuário da requisição)
- [ ] T020 [P] Escrever testes que falham dos privilégios de banco em `tests/core/test_db_privileges.py` (FR-019, FR-026: com `SET ROLE sgp_app`, UPDATE/DELETE em `audit_auditevent` e DELETE em tabelas de negócio falham; INSERT funciona)
- [ ] T021 Implementar `sgp/core/db_privileges.py` e o comando `sgp/core/management/commands/apply_db_privileges.py` (lista de tabelas append-only vinda dos modelos `AppendOnlyModel`; DELETE só em `django_session`)
- [ ] T022 [P] Escrever testes que falham de perfis e permissões em `tests/accounts/test_profiles.py` (FR-009: soma de perfis; FR-015: decorator recusa com 403 e grava `auth.permission_denied`) e da regra de projeto em `tests/core/test_access.py` (FR-014)
- [ ] T023 Implementar `sgp/accounts/profiles.py` (enum `Profile`, rótulos, `GLOBAL_PROJECT_ACCESS`, `active_profiles(user)`, `has_profile`, decorator `profile_required`) e `sgp/core/access.py` (`can_access_project(user, project)`)
- [ ] T024 Criar o layout em `sgp/core/templates/base.html`, `403.html`, `404.html`, `500.html`, `sgp/core/static/core/css/sgp.css`, a página inicial `sgp/core/views.py` (`/`) com atalhos por perfil, o context processor `sgp/core/context_processors.py` e a verificação de saúde `/saude/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Entrar com o login de rede (Priority: P1) 🎯 MVP

**Goal**: login exclusivo pela rede, cadastro alimentado pelo AD e página "Solicitar acesso" para quem não tem perfil.

**Independent Test**: entrar com uma conta com perfil (chega ao início) e outra sem perfil (só vê "Solicitar acesso"), conferindo os eventos.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T025 [P] [US1] Testes do login em `tests/accounts/test_login.py` (FR-001 senha não guardada; FR-002 criação e alteração do cadastro com valor anterior e novo; FR-004 mensagem genérica para senha errada, usuário inexistente e conta desativada; serviço indisponível; FR-027 senha ausente de eventos; FR-008 logout)
- [ ] T026 [P] [US1] Testes da pessoa sem perfil e da solicitação em `tests/accounts/test_access_request.py` (FR-003: só "Solicitar acesso" e logout; justificativa obrigatória; evento `accounts.access_requested`; redirecionamento com `auth.permission_denied`; pessoa que perde o último perfil com a sessão aberta passa a ser recusada na requisição seguinte)
- [ ] T027 [P] [US1] Testes de integração LDAP em `tests/accounts/test_ldap_integration.py` (marcador `ldap`: bind real, atributos mapeados, senha errada e conta desativada recusadas)

### Implementation for User Story 1

- [ ] T028 [US1] Implementar `LoginAttempt` (*append-only*; "result success, failure, blocked, unavailable") e `AccessRequest` ("status pending → granted ou rejected") em `sgp/accounts/models.py` com migração
- [ ] T029 [US1] Implementar `sgp/accounts/ldap.py` (montagem das settings `AUTH_LDAP_*` a partir do ambiente, receptor do sinal `ldap_error` para indisponibilidade, leitura dos grupos de rede do usuário autenticado) e a verificação de sistema `sgp/accounts/checks.py` que recusa LDAP sem `ldaps://` nem StartTLS quando `DEBUG` é falso (FR-027), com teste em `tests/accounts/test_checks.py`
- [ ] T030 [US1] Implementar o fluxo de login em `sgp/accounts/services.py` (`login_flow`: instantâneo do cadastro, `authenticate`, `LoginAttempt`, eventos de criação/alteração, encaminhamento conforme perfis)
- [ ] T031 [US1] Implementar as views, formulários e rotas de `/entrar/`, `/sair/` e `/solicitar-acesso/` em `sgp/accounts/views.py`, `sgp/accounts/forms.py`, `sgp/accounts/urls.py` e templates `sgp/accounts/templates/accounts/`
- [ ] T032 [US1] Implementar `ProfileRequiredMiddleware` em `sgp/accounts/middleware.py` e ativá-lo junto do `LoginRequiredMiddleware` em `config/settings.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Conceder e revogar perfis com motivo (Priority: P1)

**Goal**: gestão de perfis pelo Administrador com motivo, aprovação e histórico; sincronização opcional com grupos da rede; solicitações de acesso decididas.

**Independent Test**: conceder e revogar "Analista/Pesquisador", conferindo o acesso e os eventos com autor, motivo e aprovação.

### Tests for User Story 2 ⚠️

- [ ] T033 [P] [US2] Testes de concessão e revogação em `tests/accounts/test_profile_admin.py` (FR-010 motivo e aprovação obrigatórios; FR-011 histórico preservado; FR-012 último ADMIN; duplicado recusado; não ADMIN recebe 403; SC-004)
- [ ] T034 [P] [US2] Testes da sincronização com grupos em `tests/accounts/test_group_sync.py` (FR-013: concede e revoga só concessões `network_group`; manual intocada; eventos com o grupo como origem)
- [ ] T035 [P] [US2] Testes da decisão de solicitações e do comando inicial em `tests/accounts/test_access_request_admin.py` e `tests/accounts/test_grant_initial_admin.py` (FR-016; comando só sem ADMIN ativo)

### Implementation for User Story 2

- [ ] T036 [US2] Implementar `grant_profile`, `revoke_profile`, `sync_network_profiles` e `decide_access_request` em `sgp/accounts/services.py`, todos com `record_event` na mesma transação
- [ ] T037 [US2] Implementar as telas de Administração › Pessoas (lista com busca, detalhe com histórico, conceder, revogar) e › Solicitações em `sgp/accounts/views_admin.py`, `sgp/accounts/forms.py`, `sgp/accounts/urls.py` e templates
- [ ] T038 [US2] Integrar `sync_network_profiles` ao fluxo de login em `sgp/accounts/services.py`
- [ ] T039 [US2] Implementar o comando `sgp/accounts/management/commands/grant_initial_admin.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Provar que a trilha não foi adulterada (Priority: P1)

**Goal**: verificação da cadeia diária e sob demanda, com quebras apontadas e alerta.

**Independent Test**: alterar um evento direto no banco e rodar a verificação: o evento adulterado é apontado.

### Tests for User Story 3 ⚠️

- [ ] T040 [P] [US3] Testes da verificação em `tests/audit/test_verification.py` (FR-020/FR-021 e SC-003: íntegra; conteúdo alterado; exclusão no meio; inserção forjada; lacuna; exclusão do trecho final via ponto de controle; resultado gravado e evento `audit.chain_verified`; trigger impede UPDATE pela aplicação)
- [ ] T041 [P] [US3] Testes das telas e da rotina em `tests/audit/test_verification_views.py` e `tests/audit/test_tasks.py` (perfis QUALITY/ADMIN; alerta FR-022; agendamento diário configurado; comando com código de saída 1 na quebra)

### Implementation for User Story 3

- [ ] T042 [US3] Implementar `verify_chain` em `sgp/audit/services.py` (leitura em blocos, tipos de quebra `content_altered`, `chain_broken`, `sequence_gap`, `checkpoint_missing`, `checkpoint_mismatch`)
- [ ] T043 [US3] Implementar a tarefa `sgp/audit/tasks.py`, o agendamento `CELERY_BEAT_SCHEDULE` em `config/settings.py` e o comando `sgp/audit/management/commands/verify_audit_chain.py`
- [ ] T044 [US3] Implementar a tela `/auditoria/integridade/` e o POST de verificação em `sgp/audit/views.py`, `sgp/audit/urls.py` e templates; alerta global no context processor

**Checkpoint**: All P1 user stories should now be independently functional

---

## Phase 6: User Story 4 - Consultar e exportar a trilha (Priority: P2)

**Goal**: consulta filtrada da trilha e exportação CSV/XLSX auditada.

**Independent Test**: filtrar por usuário, período, projeto e tipo e exportar; o arquivo traz exatamente os eventos filtrados e a exportação aparece na trilha.

### Tests for User Story 4 ⚠️

- [ ] T045 [P] [US4] Testes da consulta em `tests/audit/test_trail_views.py` (FR-023 filtros combinados, ordem cronológica, paginação de 50, fragmento HTMX, permissões; FR-025 horário de Brasília com segundos)
- [ ] T046 [P] [US4] Testes da exportação em `tests/audit/test_exports.py` (FR-024 conteúdo igual ao da tela, bloco de identificação, CSV com BOM e `;`, XLSX, zero eventos, evento `audit.exported`)

### Implementation for User Story 4

- [ ] T047 [US4] Implementar o formulário de filtros `sgp/audit/forms.py` e a consulta em `sgp/audit/views.py` com templates `sgp/audit/templates/audit/trilha.html` e `_tabela.html` (HTMX)
- [ ] T048 [US4] Implementar `sgp/audit/exports.py` (CSV em streaming e XLSX `write_only`) e a rota `/auditoria/exportar/`

**Checkpoint**: User Story 4 functional

---

## Phase 7: User Story 5 - Sessão com expiração e bloqueio por tentativas (Priority: P2)

**Goal**: encerramento por inatividade e bloqueio de login por tentativas, com desbloqueio pelo Administrador.

**Independent Test**: com parâmetros baixos, deixar a sessão parada e errar a senha até o limite, conferindo encerramento, bloqueio, mensagens e eventos.

### Tests for User Story 5 ⚠️

- [ ] T049 [P] [US5] Testes de inatividade em `tests/accounts/test_session_timeout.py` (FR-005, SC-006: encerra após o limite, mensagem, evento `auth.session_expired`; atividade renova)
- [ ] T050 [P] [US5] Testes de bloqueio em `tests/accounts/test_lockout.py` (FR-006, FR-007, SC-006: bloqueio na N-ésima falha, tentativa bloqueada não chama o backend, fim do bloqueio, desbloqueio manual com motivo, login aceito zera a contagem, indisponibilidade não conta, usuário inexistente é bloqueado do mesmo modo e com a mesma mensagem)

### Implementation for User Story 5

- [ ] T051 [US5] Implementar `LoginLockout` em `sgp/accounts/models.py` ("bloqueio ativo = released_at IS NULL AND expires_at > agora") com migração e as regras de contagem em `sgp/accounts/services.py`
- [ ] T052 [US5] Integrar a checagem e a criação de bloqueio ao `login_flow` em `sgp/accounts/services.py`
- [ ] T053 [US5] Implementar `InactivityTimeoutMiddleware` em `sgp/core/middleware.py` e ativá-lo em `config/settings.py`
- [ ] T054 [US5] Implementar a tela Administração › Bloqueios (lista e desbloqueio com motivo) em `sgp/accounts/views_admin.py` e templates

**Checkpoint**: All user stories should now be independently functional

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T055 Escrever a varredura de rotas em `tests/core/test_route_scan.py` (SC-002: toda rota recusa anônimo, pessoa sem perfil e perfil sem permissão, exceto as rotas anônimas do contrato) e o teste do catálogo `tests/audit/test_event_catalog.py` (FR-017: todos os eventos mínimos estão registrados com rótulo em português)
- [ ] T056 [P] Implementar `scripts/rastreabilidade.py` (lê FR/SC dos `specs/*/spec.md` e o JSON do `--req-report`) e gerar `docs/validacao/matriz-rastreabilidade.md`
- [ ] T057 [P] Medir desempenho em `tests/audit/test_performance.py` (marcador `slow`: verificação de 200 mil eventos e consulta filtrada; extrapolar para SC-005 e SC-007)
- [ ] T058 Rodar a suíte completa, a cobertura (≥ 90% em `sgp.core` e `sgp.audit`) e o `ruff check`
- [ ] T059 [P] Atualizar `README.md` e `CLAUDE.md` com os comandos de execução e de teste
- [ ] T060 Executar o roteiro de `quickstart.md` no ambiente Docker (navegador e terminal) e registrar o resultado; registrar a medição do SC-001 (login ≤ 5 s) como passo manual da homologação com o AD real

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion; executadas em ordem de prioridade por um desenvolvedor (US1 → US2 → US3 → US4 → US5)
- **Polish (Final Phase)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: depende só da Fase 2
- **US2 (P1)**: depende da Fase 2; a sincronização de grupos (T038) se liga ao fluxo de login da US1
- **US3 (P1)**: depende da Fase 2 (trilha e eventos)
- **US4 (P2)**: depende da Fase 2; usa eventos gerados pelas outras histórias nos testes por fixtures próprias
- **US5 (P2)**: depende do fluxo de login da US1 (T030)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before views
- Story complete before moving to next priority

### Parallel Opportunities

- T003 a T006 e T008 (arquivos de implantação independentes)
- T010, T014, T017, T020 e T022 (testes e catálogo em arquivos diferentes)
- Testes de cada história marcados [P]

---

## Parallel Example: User Story 1

```bash
# Testes da US1 juntos:
Task: "Testes do login em tests/accounts/test_login.py"
Task: "Testes da pessoa sem perfil em tests/accounts/test_access_request.py"
Task: "Testes de integração LDAP em tests/accounts/test_ldap_integration.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently

### Incremental Delivery

1. Setup + Foundational → trilha encadeada e perfis prontos
2. US1 → login pela rede (MVP)
3. US2 → gestão de perfis
4. US3 → verificação de integridade (fecha os critérios de pronto)
5. US4 → consulta e exportação
6. US5 → sessão e bloqueio

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
