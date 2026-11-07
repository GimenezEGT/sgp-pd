# Implementation Plan: Abertura de projeto — TAP e Plano de Negócios

**Branch**: `002-abertura-projeto` | **Date**: 2026-11-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-abertura-projeto/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

O líder cria o projeto em rascunho, preenche TAP (com equipe e marcos) e Plano de Negócios (com 5
previsões anuais), submete; o Gestor de P&D aprova ou devolve com comentário. A aprovação gera o
código PD-AAAA-NNN por sequência anual no banco, abre o projeto na versão 01 e libera o acesso da
equipe. Dados financeiros têm permissão por campo aplicada em telas, listas, exportações e na
trilha de auditoria.

Abordagem técnica (entrada do `/speckit-plan`): reaproveita a base da 001 (perfis, trilha,
`ProtectedModel`, regra `can_access_project`). Nova app `projects` (projetos) com `Project`,
`ProjectCharter` (TermoAbertura), `BusinessPlan` (PlanoNegocios), `AnnualForecast`
(PrevisaoAnual, 5 linhas), `Milestone` (Marco) e `ProjectMember` (MembroProjeto), mais
`ProjectDecision` e `ProjectCodeSequence`. Valores em `Decimal(14,2)`, BRL, formato brasileiro na
tela. Máquina de estados explícita e testada. Validação no servidor e mensagens em português.
Listas controladas (tecnologia, tipo de subdocumento) numa app pequena `vocab`.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: as da feature 001 (Django 5.2 LTS, HTMX); nenhuma dependência nova

**Storage**: PostgreSQL 17; JSONB para listas e tabelas internas do TAP; sequência anual de código
em tabela própria com `INSERT … ON CONFLICT … RETURNING`

**Testing**: pytest + pytest-django, marcador `req("002:…")`; teste de concorrência com threads e
`transactional_db`

**Target Platform**: a mesma da 001 (Docker Compose na intranet)

**Project Type**: aplicação web monolítica

**Performance Goals**: lista de 200 projetos com filtros em < 2 s (SC-005)

**Constraints**: nada é apagado (membros e marcos são encerrados/cancelados); dados financeiros
nunca saem para quem não tem permissão, inclusive na trilha; transições de estado só pela máquina

**Scale/Scope**: dezenas de projetos por ano; ~12 telas

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Como o plano atende | Situação |
| --- | --- | --- |
| I. Rastreabilidade | Toda criação/edição gera evento com campos alterados; decisões em `ProjectDecision` append-only; membros e marcos sem exclusão (encerramento/cancelamento com motivo) | Atende |
| II. Trilha imutável | Usa `record_event` da 001 com `project_id`; filtro da trilha por projeto passa a listar projetos | Atende |
| III. Assinatura | Aprovação é confirmação registrada (fora do escopo; 005 troca por assinatura); líder não aprova o próprio projeto | Atende (escopo) |
| IV. Modelos versionados | Tecnologia e tipo de subdocumento são dados (`vocab`), não código | Atende |
| V. Fonte única | Nome do projeto e líder do Plano de Negócios vêm do `Project`; pessoas referenciadas por FK | Atende |
| VI. Cálculo automático | Total de 5 anos e regime calculados; código e versão gerados | Atende |
| VII. Segurança | Acesso por projeto (`can_access_project`); permissão por campo para financeiros em telas, listas, exportações e trilha (mascaramento) | Atende |
| VIII. Qualidade verificável | TDD na máquina de estados, no código anual concorrente, nas permissões financeiras e nas validações; testes marcados com requisito | Atende |
| IX. Simplicidade | Sem dependências novas; formulários do Django; nomes em inglês, telas em português | Atende |

Reavaliação pós-desenho: sem violações.

## Project Structure

### Documentation (this feature)

```text
specs/002-abertura-projeto/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── rotas-ui.md
│   ├── eventos-auditoria.md
│   └── dados-financeiros.md
└── tasks.md
```

### Source Code (repository root)

```text
sgp/
├── vocab/                    # listas controladas (Vocabulary, Term) com carga inicial
│   ├── models.py
│   └── migrations/0001_initial.py, 0002_seed.py
├── projects/
│   ├── models.py             # Project, ProjectCharter, BusinessPlan, AnnualForecast,
│   │                         # Milestone, ProjectMember, ProjectDecision, ProjectCodeSequence
│   ├── workflow.py           # máquina de estados e geração do código
│   ├── permissions.py        # acesso, edição e dados financeiros
│   ├── services.py           # criação, edição com diff, equipe, marcos, decisões
│   ├── completeness.py       # pendências para submeter
│   ├── fields.py             # campo monetário BRL
│   ├── forms.py / views.py / urls.py / event_types.py / masking.py
│   └── templates/projects/
├── audit/masking.py          # registro de campos sensíveis por tipo de evento
└── core/diff.py              # campos alterados (valor anterior e novo)
tests/projects/, tests/vocab/
```

**Structure Decision**: app `projects` (projetos, nome do plano traduzido) e app `vocab` para as
listas controladas que as features 003, 004 e 007 também usarão.

## Complexity Tracking

Sem violações da constituição a justificar.
