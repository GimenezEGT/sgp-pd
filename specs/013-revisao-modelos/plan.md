# Implementation Plan: Revisão controlada dos modelos de documentos e subdocumentos

**Branch**: `013-revisao-modelos` | **Date**: 2026-11-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/013-revisao-modelos/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Revisão controlada dos modelos de formulário (004) e de layout (006): a Qualidade/AR abre a revisão
(rascunho da próxima versão), altera, envia com motivo e impacto; o Gestor de P&D devolve com
comentário ou aprova com assinatura eletrônica e vigência imediata ou futura; a publicação vira
efeito da aprovação. Histórico com etapas, comparação entre versões, uso por versão, verificação de
integridade, descarte de rascunho e retirada de uso de modelo de subdocumento com assinatura.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: as das features anteriores (sem dependência nova)

**Storage**: PostgreSQL 17; etapas e assinaturas de modelo em tabelas somente de inclusão; campos de
revisão nas tabelas de modelos (004 e 006) por migração

**Testing**: pytest + pytest-django; diretório falso para a senha; adulteração direta no banco para
a verificação; marcador `req("013:…")`

**Target Platform**: a mesma da 001 (tarefa diária no worker Celery com agendador embutido)

**Project Type**: aplicação web monolítica

**Performance Goals**: ciclo completo em menos de 5 minutos para quem conhece a tela (SC-005)

**Constraints**: nenhuma publicação sem aprovação assinada; quem elabora não aprova; versão
publicada imutável; documentos iniciados não mudam de versão

**Scale/Scope**: 12 famílias de modelo (9 de formulário, 3 de layout), poucas versões por ano

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Como o plano atende | Situação |
| --- | --- | --- |
| I. Rastreabilidade | Cada versão registra quem elaborou, enviou, devolveu, aprovou e descartou, com motivo e impacto; nada é apagado (descarte e retirada são lógicos) | Atende |
| II. Trilha imutável | Todas as transições geram eventos; etapas somente de inclusão | Atende |
| III. Assinatura | Aprovação e retirada com reautenticação, significado, data e hora e resumo; elaborador não aprova | Atende |
| IV. Modelos versionados | É a própria feature: publicação só pela revisão controlada; documentos ficam na versão em que começaram | Atende |
| V. Fonte única | Conteúdo do modelo continua num só lugar (as tabelas de modelo das features 004 e 006) | Atende |
| VI. Cálculo automático | Comparação, resumo e verificação calculados pelo sistema | Atende |
| VII. Segurança | Perfis por etapa, negação registrada, inclusive por URL direta | Atende |
| VIII. Qualidade verificável | TDD no ciclo, nas permissões, na vigência e na adulteração | Atende |
| IX. Simplicidade | Um mixin de campos e um serviço com adaptadores para os dois tipos de modelo | Atende |

Reavaliado depois da Fase 1: sem mudanças.

## Project Structure

### Documentation (this feature)

```text
specs/013-revisao-modelos/
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/rotas-ui.md, eventos-auditoria.md
└── tasks.md
```

### Source Code (repository root)

```text
sgp/revisions/
├── models.py        # RevisableTemplate (mixin), TemplateStep, TemplateSignature, TemplateRetirement
├── adapters.py      # formulário e layout: família, versões, vigente, publicação interna, uso, conteúdo
├── diff.py          # achatamento e comparação de definições
├── services.py      # abrir (via 004/006), enviar, devolver, aprovar, descartar, verificar, retirada, vigência
├── tasks.py         # registro diário da entrada em vigência
└── views.py / urls.py / event_types.py / templates/revisions/
sgp/formtemplates/, sgp/documents/   # campos de revisão, publicação só pela aprovação, botões nas telas
tests/revisions/
```

**Structure Decision**: app `revisions` com adaptadores para os dois tipos de modelo; as apps de
modelo mantêm o conteúdo e a vigência.

## Complexity Tracking

Sem violações da constituição a justificar.
