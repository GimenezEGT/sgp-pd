# Implementation Plan: Versionamento do documento final do projeto

**Branch**: `016-versao-documento-final` | **Date**: 2026-11-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/016-versao-documento-final/spec.md`

## Summary

Registro próprio das versões do documento final de cada projeto (`FinalDocumentVersion`, somente de
inclusão): número sequencial por projeto, mudança (partes com versão anterior e nova), composição
completa (cada parte na versão aprovada vigente, com data e resumo) e resumo da composição. Uma nova
versão nasce na mesma transação de cada aprovação de parte (aprovação de subdocumento, TAP ou Plano;
aprovação do projeto gera uma versão com TAP e Plano), com evento na trilha. O documento completo
gerado (009) aponta para a versão do documento final, que aparece na capa, no nome do arquivo e num
quadro próprio; a tela do projeto mostra o histórico; cada parte mostra o próprio histórico de
versões e em quais versões do documento final entrou. As aprovações já registradas reconstroem o
histórico na migração, e cada versão reconstruída ganha evento na trilha logo depois das migrações.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: as das features 005, 006 e 009; nenhuma nova

**Storage**: PostgreSQL 17; migrações `fulldoc.0003` (modelo e referência no documento gerado),
`0004` (gatilho de imutabilidade) e `0005` (reconstrução do histórico)

**Testing**: pytest; marcador `req("016:…")`; fixtures da 009 (`signed_project`, `create_sub`,
`force_approve`, `signing`)

**Target Platform / Project Type**: os mesmos; aplicação web com worker

**Performance Goals**: registro da versão em milissegundos dentro da aprovação; composição montada
das versões aprovadas (dezenas de partes por projeto)

**Constraints**: versão do documento final só nasce com aprovação (ou recomposição/reconstrução);
registros imutáveis; numeração sem lacuna nem repetição (bloqueio da linha do projeto)

**Scale/Scope**: dezenas de versões por projeto

## Constitution Check

| Princípio | Como o plano atende | Situação |
| --- | --- | --- |
| I. Rastreabilidade | Cada versão do documento final guarda a mudança e a composição com os resumos das partes; documento gerado aponta para a versão | Atende |
| II. Trilha imutável | Evento `fulldoc.version_created` na mesma transação; versões somente de inclusão com gatilho | Atende |
| III. Assinatura | Versão do documento final nasce só de aprovação assinada (ou recomposição/reconstrução identificadas) | Atende |
| IV. Modelos versionados | Não se aplica | Atende |
| V. Fonte única | Composição montada das versões aprovadas congeladas (005/006) | Atende |
| VI. Cálculo automático | Não se aplica | Atende |
| VII. Segurança | Histórico visível a quem acessa o projeto; dados financeiros não entram (só nome, versão e resumo das partes) | Atende |
| VIII. Qualidade verificável | Testes de aprovação, aprovação do projeto, recomposição, reconstrução, geração e telas; migração com teste | Atende |
| IX. Simplicidade | Um modelo e um módulo na app da 009; sem rota nova | Atende |

## Project Structure

### Documentation (this feature)

```text
specs/016-versao-documento-final/
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/telas-e-documento.md
└── tasks.md
```

### Source Code (repository root)

```text
sgp/fulldoc/
├── models.py              # FinalDocumentVersion; FullDocument.final_version
├── versioning.py          # composição, registrar, recompor, histórico do projeto e das partes
├── history.py             # reconstrução a partir das aprovações (usada pela migração) e eventos
├── apps.py                # post_migrate: evento na trilha das versões reconstruídas
├── compose.py             # quadro "Versões do documento final"; resumo inclui a versão
├── services.py            # geração aponta para a versão; nome do arquivo e código pela versão
├── templatetags/fulldoc_versions.py  # histórico de versões de uma parte (telas da 004 e 002)
├── templates/fulldoc/     # project.html (histórico), _part_history.html, pdf/document.html (capa e quadro)
└── migrations/0003…0005
sgp/signatures/services.py # approve e approve_project registram a versão do documento final
sgp/subdocuments/templates/subdocuments/detail.html, sgp/projects/templates/projects/detail.html
tests/fulldoc/test_final_versions.py
```

**Structure Decision**: o registro mora na app do documento completo (009); a assinatura (005) chama o
registro por importação tardia, na mesma transação da aprovação.

## Complexity Tracking

Sem violações da constituição a justificar.
