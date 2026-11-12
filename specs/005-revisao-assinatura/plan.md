# Implementation Plan: Revisão, versões e assinatura eletrônica

**Branch**: `005-revisao-assinatura` | **Date**: 2026-11-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-revisao-assinatura/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Ciclo de revisão (rascunho, em revisão, devolvido, aprovado; versão anterior substituída) para
subdocumentos, TAP e Plano de Negócios, com assinatura eletrônica avançada interna: reautenticação
no AD, significado, data e hora do servidor e SHA-256 do conteúdo canônico. Versão aprovada
congelada em tabela somente de inclusão; verificação de integridade recalcula e compara; nova
versão com motivo; delegação de aprovação; bloqueio após três falhas; fila de revisão com prazo.

Abordagem técnica (entrada do `/speckit-plan`): máquina de estados por documento (rascunho, em
revisão, aprovado, devolvido, substituído) com transições permitidas por perfil e testadas. Na
assinatura, reautentique no AD por bind LDAP, sem guardar a senha. Calcule SHA-256 de uma
representação canônica do conteúdo (JSON com chaves ordenadas mais os hashes dos anexos) e grave
Assinatura com esse hash. Versão aprovada vira registro imutável (sem UPDATE por permissão de
banco). A verificação de integridade recalcula o hash e compara. Eventos de assinatura vão para a
trilha da feature 001. Limite de tentativas com bloqueio temporário.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: as das features anteriores (django-auth-ldap para a reautenticação)

**Storage**: PostgreSQL 17; versões aprovadas e assinaturas em tabelas somente de inclusão

**Testing**: pytest + pytest-django; diretório falso da 001 para senha certa, errada e AD
indisponível; adulteração direta no banco para a verificação; marcador `req("005:…")`

**Target Platform**: a mesma da 001

**Project Type**: aplicação web monolítica

**Performance Goals**: verificação de documento com 10 versões em < 2 s (SC-005)

**Constraints**: senha nunca guardada; assinatura ligada a versão e resumo; versão aprovada imutável
no banco; a aprovação continua bloqueando os cadastros referenciados (003/004)

**Scale/Scope**: dezenas de documentos por projeto, poucas versões por documento

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Como o plano atende | Situação |
| --- | --- | --- |
| I. Rastreabilidade | Versões numeradas; anterior substituída e consultável; motivo obrigatório | Atende |
| II. Trilha imutável | Envio, assinatura, falha, bloqueio, devolução, aprovação, nova versão, delegação e verificação geram eventos | Atende |
| III. Assinatura | Reautenticação, significado, data e hora do servidor e hash do conteúdo; aprovado bloqueado | Atende |
| IV. Modelos versionados | O conteúdo congelado guarda a versão de modelo usada | Atende |
| V. Fonte única | Hash cobre referências por versão aos cadastros, bloqueadas na aprovação | Atende |
| VI. Cálculo automático | Resumo e verificação calculados pelo sistema | Atende |
| VII. Segurança | Aprovação só por Gestor ou delegado; elaborador não aprova; bloqueio após falhas | Atende |
| VIII. Qualidade verificável | TDD na máquina de estados, na assinatura, na adulteração e na delegação | Atende |
| IX. Simplicidade | Um serviço de assinatura genérico com adaptadores para os três tipos de documento | Atende |

## Project Structure

### Documentation (this feature)

```text
specs/005-revisao-assinatura/
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/rotas-ui.md, eventos-auditoria.md, conteudo-canonico.md
└── tasks.md
```

### Source Code (repository root)

```text
sgp/signatures/
├── models.py        # ApprovedVersion, Signature, SignatureAttempt, SignatureLock, ReviewComment, ApprovalDelegation
├── documents.py     # adaptadores: subdocumento, TAP, Plano de Negócios (conteúdo, situação, permissões)
├── canonical.py     # JSON canônico e SHA-256
├── reauth.py        # reautenticação no AD, tentativas e bloqueio
├── services.py      # enviar, revisar, aprovar, devolver, nova versão, verificar, delegação
└── views.py / forms.py / urls.py / templates/signatures/
sgp/subdocuments/, sgp/projects/   # situações novas e integração (aprovação provisória substituída)
tests/signatures/
```

**Structure Decision**: app `signatures` com adaptadores por tipo de documento; subdocumentos e
projetos chamam os serviços dela.

## Complexity Tracking

Sem violações da constituição a justificar.
