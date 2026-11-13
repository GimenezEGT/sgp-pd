# Implementation Plan: Correções do ciclo de revisão e assinatura

**Branch**: `015-correcoes-revisao-assinatura` | **Date**: 2026-11-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/015-correcoes-revisao-assinatura/spec.md`

## Summary

Correção da feature 005 em três pontos: (1) assinatura "Revisado" única por pessoa e versão, no
serviço (recusa com mensagem) e na tela (a opção some); (2) Gestor que elaborou: aviso e devolução
no bloco de assinaturas do documento, seção própria na Fila de revisão, aviso na tela de envio e,
na tela de aprovação, sem o formulário de aprovação para quem elaborou; (3) situação pelo nome nas
telas de envio e aprovação. Sem modelo de dados novo, sem rota nova.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: as da feature 005 (Django 5.2, HTMX); nenhuma nova

**Storage**: PostgreSQL 17, sem migração (assinaturas, comentários e delegações da 005)

**Testing**: pytest; marcador `req("015:…")`; fixtures da 005 (`signing`, Entrada completa)

**Target Platform / Project Type**: os mesmos; aplicação web

**Performance Goals**: sem mudança

**Constraints**: regras da 005 inalteradas (segregação, devolução com comentário, assinaturas
imutáveis); textos em português

**Scale/Scope**: três telas (bloco de assinaturas, envio/aprovação, Fila de revisão) e dois serviços

## Constitution Check

| Princípio | Como o plano atende | Situação |
| --- | --- | --- |
| I. Rastreabilidade | Devolução e assinaturas continuam na trilha; nenhuma assinatura gravada é alterada | Atende |
| II. Trilha imutável | Sem mudança | Atende |
| III. Assinatura | Revisão única por pessoa e versão; segregação mantida e explicada na tela | Atende |
| IV a VI | Não se aplicam | Atende |
| VII. Segurança | Devolução só para quem tem poder de aprovação e acesso ao projeto, como na 005 | Atende |
| VIII. Qualidade verificável | Testes para cada FR; rotas existentes no contrato | Atende |
| IX. Simplicidade | Sem rota nem modelo novo | Atende |

## Project Structure

### Documentation (this feature)

```text
specs/015-correcoes-revisao-assinatura/
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/telas.md   # mudanças de comportamento nas telas existentes
└── tasks.md
```

### Source Code (repository root)

```text
sgp/signatures/
├── services.py    # sign_review único por pessoa e versão; block_context (can_review, own_submission,
│                  # can_return_own, status_label); review_queue(own=True)
├── documents.py   # STATUS_LABELS
├── views.py       # contexto de envio/aprovação com status_label e aviso; fila com seção própria
└── templates/signatures/  _block.html, sign.html, queue.html
tests/signatures/test_correcoes_015.py
```

**Structure Decision**: correção dentro da app da feature 005.

## Complexity Tracking

Sem violações da constituição a justificar.
