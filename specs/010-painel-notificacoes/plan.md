# Implementation Plan: Painel do gestor e notificações

**Branch**: `010-painel-notificacoes` | **Date**: 2026-11-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/010-painel-notificacoes/spec.md`

## Summary

Painel da carteira de projetos (quatro totais e, por projeto, etapa atual, percentual de
subdocumentos aprovados, marcos planejados × realizados, atraso e líder; custo e retorno só com
permissão financeira), linha do tempo do projeto a partir da trilha, fila do gestor (a da 005),
"Minhas pendências" para cada pessoa, exportação XLSX e notificações por e-mail: imediatas na
devolução e na aprovação de documento e resumo diário às 7h com as pendências vencidas, com
preferências por tipo (assinatura pendente sempre ligada).

Abordagem técnica (entrada do `/speckit-plan`): consultas agregadas com índices dedicados e cache de
5 minutos; gráficos simples em SVG gerado no servidor, sem build de front-end; e-mails pelo SMTP
interno em tarefa agendada (Celery beat), com resumo diário; exportação XLSX com openpyxl.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: as anteriores (Django, Celery beat, openpyxl); `django.core.mail` com o
SMTP interno; nenhuma nova

**Storage**: PostgreSQL 17 (preferências e notificações); cache do Django (Redis em produção via
`CACHE_URL`, memória local sem ele)

**Testing**: pytest (`mail.outbox`, tempo simulado); marcador `req("010:…")`

**Target Platform / Project Type**: os mesmos; aplicação web com worker e beat

**Performance Goals**: painel com 100 projetos em < 2 s (SC-001)

**Constraints**: o painel e a planilha respeitam a regra única de acesso e a permissão financeira;
e-mails em português, sem dados financeiros; segredos do SMTP só em variáveis de ambiente

**Scale/Scope**: centenas de projetos, dezenas de pessoas

## Constitution Check

| Princípio | Como o plano atende | Situação |
| --- | --- | --- |
| I. Rastreabilidade | Linha do tempo lida da trilha; notificações guardam o registro de origem | Atende |
| II. Trilha imutável | Envio, falha, omissão, preferência e exportação geram eventos | Atende |
| III. Assinatura | Assinatura pendente nunca pode ser desligada | Atende |
| IV. Modelos versionados | Não altera modelos | Atende |
| V. Fonte única | Indicadores calculados dos registros (versões aprovadas, marcos, caderno, fila da 005), sem cópia | Atende |
| VI. Cálculo automático | Percentual, atraso e esperas calculados pelo sistema | Atende |
| VII. Segurança | Regra única de acesso; custo e retorno só com permissão; e-mail sem dado financeiro | Atende |
| VIII. Qualidade verificável | Testes de indicadores, permissões, e-mails (imediato e resumo), preferências e desempenho | Atende |
| IX. Simplicidade | Consultas agregadas e SVG no template; sem biblioteca de gráficos | Atende |

## Project Structure

```text
specs/010-painel-notificacoes/  plan.md, research.md, data-model.md, quickstart.md, contracts/, tasks.md
sgp/dashboard/
├── portfolio.py    # carteira e totais (consultas agregadas, cache)
├── timeline.py     # linha do tempo do projeto a partir da trilha
├── pending.py      # minhas pendências
├── export.py       # XLSX
└── views.py / urls.py / event_types.py / templates/dashboard/
sgp/notifications/
├── models.py       # NotificationPreference, Notification
├── recipients.py   # quem recebe cada evento
├── services.py     # criar, enviar (com novas tentativas), resumo diário, preferências
├── signals.py      # eventos da trilha que geram e-mail imediato
└── tasks.py / views.py / urls.py / event_types.py / templates/notifications/
tests/dashboard/, tests/notifications/
```

## Complexity Tracking

Sem violações da constituição a justificar.
