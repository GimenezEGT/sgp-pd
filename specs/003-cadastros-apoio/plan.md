# Implementation Plan: Cadastros de apoio

**Branch**: `003-cadastros-apoio` | **Date**: 2026-11-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-cadastros-apoio/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Cadastros únicos e versionados de lotes (por projeto), insumos, kits de referência, amostras,
painéis, normas e referências bibliográficas, referenciados por versão nos documentos. Correção
no próprio registro enquanto não houver documento assinado; depois do bloqueio, nova versão com
motivo. Anexos com SHA-256 conferido na leitura, importação de insumos com pré-visualização e
relatório de rejeições, busca enquanto digita e manutenção das listas controladas pela Qualidade.

Abordagem técnica (entrada do `/speckit-plan`): app `catalog` (cadastros) com `Lot`, `Material`
(Insumo), `ReferenceKit`, `Sample` (Amostra), `Panel`, `Standard` (Norma) e
`BibliographicReference` (Referencia). Amostras identificadas só por código interno, sem dados
pessoais. Anexos numa app `files` com hash SHA-256 conferido na leitura. Importação CSV/XLSX com
pré-visualização, validação linha a linha e relatório de rejeições. Autocomplete com HTMX.
Histórico por entidade e bloqueio de alteração in-place quando o registro está referenciado em
versão assinada (correção cria nova versão).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: as das features anteriores (Django 5.2, HTMX, openpyxl); extensão
`pg_trgm` do PostgreSQL para a busca por trecho

**Storage**: PostgreSQL 17 (uma tabela por cadastro, cada linha é uma versão); arquivos em
`MEDIA_ROOT` endereçados pelo SHA-256 (volume `media` no Compose)

**Testing**: pytest + pytest-django; marcador `req("003:…")`; importação de 500 linhas e busca
com 10 mil insumos medidas nos testes

**Target Platform**: a mesma da 001

**Project Type**: aplicação web monolítica

**Performance Goals**: busca < 1 s com 10 mil insumos (SC-004); importação de 500 linhas < 30 s
(SC-002)

**Constraints**: nada é apagado; referência sempre a uma versão; nenhum dado pessoal de paciente;
arquivos conferidos a cada leitura

**Scale/Scope**: milhares de insumos, centenas de lotes, amostras e normas; ~15 telas genéricas

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Como o plano atende | Situação |
| --- | --- | --- |
| I. Rastreabilidade | Cada linha é uma versão com autor, data, motivo; versões antigas intactas; desativação em vez de exclusão | Atende |
| II. Trilha imutável | Criação, correção, nova versão, bloqueio, desativação, importação, upload e falha de integridade de arquivo geram eventos | Atende |
| III. Assinatura | Mecanismo de bloqueio pronto para a 005 (assinar trava as versões referenciadas) | Atende (preparação) |
| IV. Modelos versionados | Listas controladas mantidas pela Qualidade com versão; cadastros versionados | Atende |
| V. Fonte única | Documentos referenciam a versão do cadastro; nada é redigitado | Atende |
| VI. Cálculo automático | Exibição padronizada do lote; contagens da importação calculadas | Atende |
| VII. Segurança | Lotes respeitam o acesso por projeto; edição só por perfis autorizados; LGPD nas amostras; arquivos com tipo e tamanho limitados | Atende |
| VIII. Qualidade verificável | TDD no versionamento, bloqueio, LGPD, importação e integridade de arquivos | Atende |
| IX. Simplicidade | Um mecanismo genérico de versão e de telas para os sete cadastros; sem dependências novas | Atende |

## Project Structure

### Documentation (this feature)

```text
specs/003-cadastros-apoio/
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/rotas-ui.md, eventos-auditoria.md, importacao-insumos.md
└── tasks.md
```

### Source Code (repository root)

```text
sgp/
├── files/                 # StoredFile (append-only), armazenamento por SHA-256, leitura conferida
├── catalog/
│   ├── models.py          # VersionedRecord (abstrato) + os sete cadastros + ImportBatch
│   ├── versioning.py      # criar, corrigir (no lugar ou nova versão), bloquear, desativar
│   ├── lgpd.py            # validadores de dados pessoais das amostras
│   ├── importing.py       # leitura CSV/XLSX, validação linha a linha, confirmação, relatório
│   ├── kinds.py           # registro dos tipos de cadastro para as telas genéricas
│   ├── forms.py / views.py / urls.py / event_types.py
│   └── templates/catalog/
└── vocab/views.py, forms.py, services.py   # manutenção das listas pela Qualidade
tests/catalog/, tests/files/, tests/vocab/
```

**Structure Decision**: app `catalog` (cadastros, nome do plano traduzido) e app `files`
reutilizável pelas features 004, 006 e 008.

## Complexity Tracking

Sem violações da constituição a justificar.
