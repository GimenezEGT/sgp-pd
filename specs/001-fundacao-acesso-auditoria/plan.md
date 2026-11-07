# Implementation Plan: Fundação — acesso, perfis e trilha de auditoria

**Branch**: `001-fundacao-acesso-auditoria` | **Date**: 2026-11-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-fundacao-acesso-auditoria/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Entregar o esqueleto seguro do SGP-P&D: login exclusivo pelo Active Directory (LDAP), cadastro de
pessoas alimentado pela rede, seis perfis concedidos e revogados com motivo e aprovação, regra única
de acesso por projeto, expiração de sessão por inatividade, bloqueio por tentativas inválidas e uma
trilha de auditoria append-only encadeada por SHA-256, verificada diariamente e sob demanda, com
consulta filtrada e exportação CSV/XLSX.

Abordagem técnica (entrada do `/speckit-plan`): Python 3.12 e Django 5.2 LTS, PostgreSQL 17, templates
do Django com HTMX (sem SPA), django-auth-ldap com grupos do AD mapeados para perfis, sessões no
servidor, trilha em tabela sem UPDATE/DELETE para o usuário de banco da aplicação, hash SHA-256 do
evento anterior em cada evento e rotina diária de verificação. Datas em UTC no banco, exibidas em
America/Sao_Paulo. Monólito modular com as apps `core`, `accounts` (contas) e `audit` (auditoria).
Testes com pytest e pytest-django, cobertura mínima de 90% em `core` e `audit`. Docker Compose com
app, banco e Nginx com TLS interno; configuração por variáveis de ambiente, sem segredos no
repositório.

## Technical Context

**Language/Version**: Python 3.12 (imagem `python:3.12-slim-bookworm`)

**Primary Dependencies**: Django 5.2 LTS (5.2.19), django-auth-ldap 5.4 + python-ldap 3.4, psycopg 3.3,
Celery 5.7 + Redis 7.4 (rotina diária), gunicorn, WhiteNoise, openpyxl (XLSX), HTMX 2.0.11 (arquivo
estático local)

**Storage**: PostgreSQL 17 (≥ 16 exigido); dois papéis de banco: dono do esquema (migrações) e
aplicação (sem DELETE, sem UPDATE nas tabelas append-only)

**Testing**: pytest 9, pytest-django 4.14, pytest-cov 7; marcador `req` para rastreabilidade
requisito → teste; marcador `ldap` para integração com servidor LDAP de desenvolvimento

**Target Platform**: VM Linux na intranet com Docker Compose; Nginx com TLS interno na frente da
aplicação; navegador corporativo

**Project Type**: aplicação web monolítica (renderização no servidor)

**Performance Goals**: login em até 5 s (p95) com o AD disponível; consulta filtrada e exportação
de um mês em < 1 min com 500 mil eventos; verificação de 1 milhão de eventos em < 15 min

**Constraints**: nada é apagado; horário do servidor; dados não saem da intranet; sem contas locais;
sem JavaScript inline (CSP `default-src 'self'`); interface em pt-BR

**Scale/Scope**: dezenas de usuários simultâneos, centenas de pessoas cadastradas, ~500 mil
eventos/ano; ~10 telas nesta feature

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Como o plano atende | Situação |
| --- | --- | --- |
| I. Rastreabilidade (ALCOA+) | Todo evento com autor, horário do servidor (UTC), objeto e origem; cadastros sem exclusão física (modelo base que recusa `delete()` + papel de banco sem DELETE); correções por novos registros | Atende |
| II. Trilha imutável | `AuditEvent` append-only: trigger contra UPDATE/DELETE, papel da aplicação só com INSERT/SELECT, encadeamento SHA-256 com sequência sem lacunas, pontos de controle e verificação diária e sob demanda | Atende |
| III. Assinatura eletrônica | Fora do escopo (feature 005); a reautenticação LDAP fica isolada em `accounts.ldap` para reuso | N/A nesta feature |
| IV. Modelos versionados | Fora do escopo (features 004 e 006) | N/A nesta feature |
| V. Fonte única | Pessoas cadastradas uma vez, a partir do AD, e referenciadas por chave; a trilha guarda o login como instantâneo | Atende |
| VI. Cálculo e numeração automáticos | Sequência da trilha calculada pelo sistema; nenhum campo calculado é digitável | Atende |
| VII. Segurança | Só AD; menor privilégio por perfil; regra única de acesso por projeto; HTTPS interno; segredos em variáveis de ambiente; LDAPS/StartTLS configurável; CSP e cookies seguros | Atende |
| VIII. Qualidade verificável | TDD nas regras de cadeia, bloqueio, permissões e sessão; cada teste marcado com o requisito; matriz de rastreabilidade gerada por script; cobertura ≥ 90% em `core` e `audit` | Atende |
| IX. Simplicidade | Monólito Django, sem SPA, sem admin do Django; identificadores em inglês e interface em pt-BR; Celery entra já nesta feature só para a rotina diária, porque é a pilha prevista para todas as tarefas de fundo | Atende (ver research R10) |

Reavaliação pós-desenho (Fase 1): sem violações; nenhuma entrada em Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/001-fundacao-acesso-auditoria/
├── plan.md              # Este arquivo
├── research.md          # Fase 0: decisões técnicas
├── data-model.md        # Fase 1: entidades, regras e privilégios de banco
├── quickstart.md        # Fase 1: roteiro de execução e validação
├── contracts/
│   ├── rotas-ui.md          # telas e rotas, perfis exigidos e eventos gerados
│   ├── eventos-auditoria.md # catálogo de eventos e formato canônico do hash
│   ├── exportacao-trilha.md # layout dos arquivos CSV e XLSX
│   └── configuracao.md      # variáveis de ambiente
└── tasks.md             # Fase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
config/                     # projeto Django: settings, urls, wsgi, celery
├── settings.py
├── settings_test.py
├── urls.py
├── wsgi.py
└── celery.py
sgp/
├── core/                   # base comum: modelos protegidos, acesso por projeto, middleware, layout
│   ├── models.py           # ProtectedModel / AppendOnlyModel
│   ├── access.py           # regra única de acesso por projeto
│   ├── middleware.py       # inatividade de sessão
│   ├── db_privileges.py    # aplicação dos privilégios do papel da aplicação
│   ├── management/commands/apply_db_privileges.py
│   ├── templates/          # base.html, 403/404/500, início
│   └── static/core/        # css, htmx.min.js
├── accounts/               # pessoas, perfis, login, bloqueio, solicitações de acesso
│   ├── models.py
│   ├── profiles.py         # perfis, permissões e decorators
│   ├── ldap.py             # configuração e sinais do django-auth-ldap
│   ├── services.py         # concessão, revogação, sincronização, bloqueio
│   ├── views.py / forms.py / urls.py / middleware.py
│   └── management/commands/grant_initial_admin.py
└── audit/                  # trilha de auditoria
    ├── models.py           # AuditEvent, ChainVerification
    ├── chain.py            # serialização canônica e hash
    ├── services.py         # record_event, verify_chain
    ├── event_types.py      # catálogo de eventos
    ├── exports.py          # CSV e XLSX
    ├── tasks.py            # rotina diária (Celery)
    ├── views.py / forms.py / urls.py
    └── management/commands/verify_audit_chain.py
tests/                      # pytest: tests/<app>/test_*.py + conftest.py
scripts/
└── rastreabilidade.py      # matriz requisito → teste (evidência de validação)
deploy/
├── docker/Dockerfile, entrypoint.sh
├── nginx/Dockerfile, nginx.conf, 10-certificado-dev.sh
├── postgres/initdb/01-papeis.sh
└── ldap-dev/seed.ldif      # usuários e grupos fictícios só para desenvolvimento
docker-compose.yml          # serviços da aplicação (base para homologação e produção)
docker-compose.override.yml # desenvolvimento: LDAP de teste, código montado, runserver
pyproject.toml / uv.lock
.env.example
```

**Structure Decision**: monólito Django com apps em `sgp/` e testes em `tests/` espelhando as apps.
As apps seguem os nomes do plano traduzidos para inglês (princípio IX): contas → `accounts`,
auditoria → `audit`. As features seguintes acrescentam apps no mesmo pacote.

## Complexity Tracking

Sem violações da constituição a justificar.
