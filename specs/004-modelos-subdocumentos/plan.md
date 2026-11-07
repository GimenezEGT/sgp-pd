# Implementation Plan: Modelos de formulário versionados e subdocumentos

**Branch**: `004-modelos-subdocumentos` | **Date**: 2026-11-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-modelos-subdocumentos/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Modelos de formulário versionados (definição em JSON validada por JSON Schema próprio, imutável
depois de publicada) e subdocumentos do projeto preenchidos em formulários montados no servidor a
partir da versão de modelo usada, com dados em JSONB conferidos contra a definição. Carga inicial
dos nove modelos versão 05. Entrada com requisitos "aplica / não se aplica", Validação com
pendências, Verificação Final gerada da Entrada aprovada, Saída com setores e itens MAPA,
Alteração que sobe a versão do projeto e marca subdocumentos para revisão, aviso de ordem do fluxo
com autorização do Gestor de P&D e aprovação provisória (confirmação registrada) até a feature 005.

Abordagem técnica (entrada do `/speckit-plan`): app "formularios" com ModeloFormulario versionado
e imutável após publicação; a definição (tópicos, campos, tipos, regras) fica em JSON validado por
um JSON Schema próprio. App "subdocumentos" com Subdocumento e dados em JSONB validados contra a
definição do modelo usado. Formulários gerados no servidor a partir da definição, com HTMX para
tabelas editáveis e autocomplete de cadastros. Carga inicial dos modelos versão 05 a partir de
docs/contexto/02-dicionario-documentos.md, por migração de dados. Testes do JSON Schema e de cada
tipo de campo. Controle otimista de concorrência na edição.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: as das features anteriores; nova: `jsonschema` (validação da definição
dos modelos pelo JSON Schema próprio, pedido do plano)

**Storage**: PostgreSQL 17; definição do modelo e dados do subdocumento em JSONB; anexos pela app
`files` (feature 003)

**Testing**: pytest + pytest-django; marcador `req("004:…")`; teste do JSON Schema, de cada tipo
de campo e das regras de fluxo

**Target Platform**: a mesma da 001

**Project Type**: aplicação web monolítica

**Performance Goals**: gravar subdocumento com 100 linhas de tabela em < 2 s (SC-005)

**Constraints**: modelo publicado imutável (serviço e gatilho no banco); nada é apagado; dados
validados no servidor; referências a cadastros por versão; acesso pela regra única de projetos

**Scale/Scope**: 9 tipos de subdocumento, ~70 tópicos, dezenas de projetos; 10 tipos de campo e
4 tipos derivados

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Como o plano atende | Situação |
| --- | --- | --- |
| I. Rastreabilidade | Subdocumento guarda autor, datas, versão de modelo e versão do documento; migração guarda o que não couber | Atende |
| II. Trilha imutável | Criação, edição (valor anterior e novo), migração, autorização de fluxo, aprovação e publicação de modelo geram eventos | Atende |
| III. Assinatura | Aprovação provisória (confirmação registrada, como na 002) até a 005; aprovado fica bloqueado e bloqueia os cadastros referenciados | Atende (provisório) |
| IV. Modelos versionados | Definição versionada em JSON com schema; publicado imutável; cada documento guarda a versão usada | Atende |
| V. Fonte única | Campos de referência apontam para versões de cadastros; Verificação Final e pendências derivadas da Entrada | Atende |
| VI. Cálculo e numeração | Numeração de tópicos e tabelas calculada; totais de colunas numéricas calculados | Atende |
| VII. Segurança | Edição só por membros (Analista, Líder) e Gestor de P&D; modelos só pela Qualidade; anexos pela política do projeto | Atende |
| VIII. Qualidade verificável | TDD no schema, em cada tipo de campo, no "não aplicável", no fluxo e na migração | Atende |
| IX. Simplicidade | Um renderizador e um validador genéricos por tipo de campo; uma dependência nova (jsonschema), pedida pelo plano | Atende |

## Project Structure

### Documentation (this feature)

```text
specs/004-modelos-subdocumentos/
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/rotas-ui.md, eventos-auditoria.md, definicao-modelo.md
└── tasks.md
```

### Source Code (repository root)

```text
sgp/
├── formtemplates/              # "formularios": FormTemplate, schema, seed versão 05, telas da Qualidade
│   ├── schema.py               # JSON Schema próprio + regras semânticas (rótulos e chaves únicos)
│   ├── fieldtypes.py           # registro dos tipos de campo: validar, resumir, vazio, referências
│   ├── seed_v05.py             # definições versão 05 (docs/contexto/02-dicionario-documentos.md)
│   └── services.py / views.py / forms.py / urls.py / templates/
├── subdocuments/               # "subdocumentos": Subdocument, FlowAuthorization
│   ├── services.py             # criar, gravar, migrar, autorizar, aprovar
│   ├── flow.py                 # ordem recomendada e pré-requisitos
│   ├── derived.py              # Verificação Final, pendências da Validação, marcos
│   ├── rendering.py / parsing.py   # formulário a partir da definição e leitura do POST
│   ├── numbering.py            # tópicos e tabelas
│   └── views.py / urls.py / templates/
└── vocab/ (novas listas do 05-vocabularios)
tests/formtemplates/, tests/subdocuments/
```

**Structure Decision**: duas apps, como no plano (`formtemplates` = "formularios",
`subdocuments` = "subdocumentos"), sobre `catalog`, `files` e `projects`.

## Complexity Tracking

Sem violações da constituição a justificar.
