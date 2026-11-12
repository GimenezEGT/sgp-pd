# Implementation Plan: Caderno de laboratório eletrônico

**Branch**: `008-caderno-laboratorio` | **Date**: 2026-11-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/008-caderno-laboratorio/spec.md`

## Summary

Caderno de laboratório por projeto e por pesquisador: entradas numeradas com data e hora do
servidor, textos formatados (objetivo, hipótese, procedimento, resultados e conclusão), materiais
ligados à versão dos cadastros da 003 (lotes, insumos e amostras), anexos com resumo SHA-256 e
imagens coladas no texto; modelos de entrada versionados; assinatura do autor e da testemunha com a
reautenticação da 005 (tentativas e bloqueio), bloqueio da entrada assinada e correção só por adendo
assinado; vínculos lógicos a subdocumentos, lotes e estudos; promoção de um anexo CSV/XLSX para um
estudo da 007 pela importação existente; linha do tempo paginada com HTMX, busca textual em
português, filtros por lote, amostra, pesquisador, período e situação, e entradas atrasadas.

Abordagem técnica (entrada do `/speckit-plan`): app "caderno" com Entrada, Adendo, ModeloEntrada,
Vínculo e Anexo; editor de texto rico com sanitização no servidor (lista branca de tags) e colagem de
imagens; anexos com hash e limite de tamanho configurável; assinatura e bloqueio reaproveitando a
feature 005; busca textual com o full-text search do PostgreSQL em português; linha do tempo paginada
com HTMX.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: as anteriores (Django 5.2, HTMX, openpyxl), mais `nh3` (sanitização de HTML
por lista branca, ligação do ammonia em Rust) no runtime

**Storage**: PostgreSQL 17 (texto de busca guardado e `tsvector` gerado com índice GIN; conteúdo
formatado como HTML sanitizado); anexos no armazenamento por SHA-256 da 003

**Testing**: pytest; marcador `req("008:…")`; teste de desempenho da busca com 1.000 entradas

**Target Platform / Project Type**: os mesmos; aplicação web monolítica

**Performance Goals**: busca num caderno de 1.000 entradas em < 2 s (SC-004); linha do tempo em
páginas de 20 entradas

**Constraints**: CSP sem estilos nem scripts inline (o editor é um arquivo estático próprio, sem
biblioteca externa); nenhum HTML do usuário sem sanitização; entrada assinada não muda (serviço e
gatilho no banco); data e hora sempre do servidor

**Scale/Scope**: centenas de entradas por projeto, alguns anexos por entrada

## Constitution Check

| Princípio | Como o plano atende | Situação |
| --- | --- | --- |
| I. Rastreabilidade | Entrada numerada por projeto; materiais pela versão do cadastro; vínculos e retiradas lógicas com quem e quando | Atende |
| II. Trilha imutável | Criação, gravação, anexo, material, assinatura, testemunho, adendo, vínculo, promoção e modelos geram eventos | Atende |
| III. Assinatura | Reautenticação da 005; resumo canônico do conteúdo na assinatura; testemunha diferente do autor | Atende |
| IV. Modelos versionados | Modelos de entrada com nova versão a cada alteração; a entrada guarda a versão usada | Atende |
| V. Fonte única | Materiais e vínculos apontam os registros dos cadastros, subdocumentos e estudos; promoção usa a importação da 007 | Atende |
| VI. Cálculo automático | A promoção leva os dados para o estudo, que calcula; o caderno não guarda resultado calculado | Atende |
| VII. Segurança | Criação pelos editores do projeto; leitura pela regra única de acesso; HTML sanitizado por lista branca; anexos só a quem acessa o projeto | Atende |
| VIII. Qualidade verificável | Testes das regras de bloqueio, sanitização, busca e promoção | Atende |
| IX. Simplicidade | Um editor estático pequeno (sem dependência de front-end); busca no próprio PostgreSQL | Atende |

## Project Structure

```text
specs/008-caderno-laboratorio/  plan.md, research.md, data-model.md, quickstart.md, contracts/, tasks.md
sgp/notebook/
├── models.py       # NotebookEntry, EntryMaterial, EntryAttachment, Addendum, NotebookSignature,
│                   # EntryTemplate, NotebookLink
├── richtext.py     # sanitização por lista branca (nh3), texto puro para a busca
├── content.py      # conteúdo canônico da entrada e do adendo (resumo assinado)
├── permissions.py  # quem cria, edita, assina, testemunha, marca relevância e mantém modelos
├── services.py     # criar, gravar, materiais, anexos, assinar, testemunhar, adendo, vínculos, modelos
├── promotion.py    # anexo CSV/XLSX → pré-visualização e confirmação da importação da 007
├── search.py       # filtros, busca textual e situação (atrasada, aguardando testemunha)
├── views.py / forms.py / urls.py / event_types.py / templates/notebook/
└── static/notebook/editor.js   # editor de texto formatado e colagem de imagens
sgp/subdocuments, sgp/studies, sgp/catalog   # vínculos mostrados nos dois sentidos
tests/notebook/
```

## Complexity Tracking

Sem violações da constituição a justificar.
