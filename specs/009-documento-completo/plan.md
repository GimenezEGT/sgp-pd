# Implementation Plan: Documento completo do projeto

**Branch**: `009-documento-completo` | **Date**: 2026-11-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/009-documento-completo/spec.md`

## Summary

Registro histórico do projeto (RDC 665/2022, art. 61) montado com um clique: capa geral, sumário
com as páginas reais, TAP, Plano de Negócios (campos financeiros só com permissão), subdocumentos
aprovados na versão vigente com as suas capas, Alterações de Projeto, Verificação Final, Saída,
quadro de versões, resumo da trilha, histórico do caderno (completo ou resumido) e lista de anexos;
pendências listadas antes de gerar; com pendências sai rascunho com marca d'água, sem pendências sai
oficial (PDF/A-2b, selo e código de verificação), arquivado com resumo SHA-256; geração assíncrona
com progresso e reaproveitamento quando nada mudou.

Abordagem técnica (entrada do `/speckit-plan`): reutilizar o gerador da feature 006 como composição
de seções; geração assíncrona com barra de progresso; reaproveitar o que já foi gerado quando a
versão não mudou (cache por hash); sumário com a numeração real das páginas, em duas passagens se a
abordagem exigir; meta de 300 páginas em menos de 3 minutos no servidor de homologação.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: as anteriores (WeasyPrint, pyHanko, Celery, HTMX); nenhuma nova

**Storage**: PostgreSQL 17 (pedidos e documentos completos arquivados); PDF no armazenamento por
SHA-256 da 003

**Testing**: pytest (pypdf para conferir sumário, páginas e texto); marcador `req("009:…")`; teste
de 300 páginas marcado `slow`

**Target Platform / Project Type**: os mesmos; aplicação web monolítica com worker Celery

**Performance Goals**: 300 páginas em < 3 min (SC-003)

**Constraints**: só conteúdo congelado na aprovação entra no corpo; o PDF oficial é determinístico
(mesmo conteúdo, mesmo arquivo antes do selo); nenhuma busca de recurso externo na renderização
(imagens do caderno embutidas)

**Scale/Scope**: dezenas de subdocumentos e centenas de entradas do caderno por projeto

## Constitution Check

| Princípio | Como o plano atende | Situação |
| --- | --- | --- |
| I. Rastreabilidade | Documento arquivado com versão do projeto, opções, pendências, resumo da composição e código de verificação | Atende |
| II. Trilha imutável | Pedido, geração, reaproveitamento, falha e download geram eventos; documento somente de inclusão | Atende |
| III. Assinatura | Corpo só com conteúdo congelado na aprovação assinada; quadro com os signatários de cada versão | Atende |
| IV. Modelos versionados | Usa o layout vigente da 006 e as capas congeladas de cada versão | Atende |
| V. Fonte única | Partes vêm do conteúdo congelado (006), das assinaturas (005), do caderno (008) e da trilha (001) | Atende |
| VI. Cálculo automático | Tabelas de estudos entram como foram congeladas; nada é recalculado | Atende |
| VII. Segurança | Gera: líder e Gestor; baixa: acesso ao projeto, e o documento com dados financeiros só quem tem a permissão | Atende |
| VIII. Qualidade verificável | Testes de ordem, sumário x páginas, pendências, rascunho x oficial, máscara financeira e desempenho | Atende |
| IX. Simplicidade | Um HTML único renderizado pelo WeasyPrint; sem juntar nem carimbar PDFs | Atende |

## Project Structure

```text
specs/009-documento-completo/  plan.md, research.md, data-model.md, quickstart.md, contracts/, tasks.md
sgp/fulldoc/
├── models.py       # FullDocumentRequest, FullDocument
├── pending.py      # pendências (subdocumentos, versões sem conteúdo congelado, Verificação Final)
├── compose.py      # partes na ordem do contrato, quadro de versões, trilha, caderno, anexos
├── render.py       # HTML único + CSS do layout vigente, sumário por target-counter, PDF/A-2b
├── services.py     # pedir, gerar (progresso, reaproveitamento, selo), baixar, verificação
├── tasks.py / views.py / urls.py / event_types.py / templates/fulldoc/
sgp/documents/templates/documents/pdf/_cover.html, _sections.html   # capa e tópicos reaproveitados
sgp/documents/services.py      # consulta do código de verificação também nos documentos completos
tests/fulldoc/
```

## Complexity Tracking

Sem violações da constituição a justificar.
