# Implementation Plan: Dossiê técnico para a ANVISA

**Branch**: `011-dossie-tecnico` | **Date**: 2026-11-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/011-dossie-tecnico/spec.md`

## Summary

Dossiê técnico montado dos dados aprovados do projeto (ou da família) na estrutura I a XII:
checagem item a item para a classe de risco (completo, faltando, não aplicável com
justificativa, com a origem do dado), geração em DOCX e PDF no formato do contexto (cabeçalho e
rodapé em itálico, itens em romanos, letras e números, tabelas numeradas, nome do produto em
itálico, declaração do responsável técnico e legal), pacote com os anexos, biblioteca de textos
padrão aprovados e versionados, complementos por projeto para o que não vem de dados, registro
do envio e do resultado e aditamento com o que mudou desde a última versão enviada.

Abordagem técnica (entrada do `/speckit-plan`): app "dossie" com a definição do dossiê (itens,
aplicabilidade por classe e mapeamento item → fonte de dados) em arquivo declarativo (YAML) que a
Qualidade ajusta sem programar, biblioteca de textos versionada e submissão; reaproveitar o gerador
da feature 006; comparação entre versões por item (texto e tabelas) para aditamentos; testes que
geram o dossiê de exemplo e comparam a árvore de títulos com a estrutura de referência.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: as anteriores (WeasyPrint, python-docx), mais PyYAML (definição
declarativa)

**Storage**: PostgreSQL 17 (definições, textos, complementos, versões do dossiê e envios);
arquivos (PDF, DOCX e pacote ZIP) no armazenamento por SHA-256 da 003

**Testing**: pytest (árvore de títulos do PDF e do DOCX, checagem por classe, diff do aditamento);
marcador `req("011:…")`

**Target Platform / Project Type**: os mesmos; aplicação web monolítica

**Performance Goals**: dossiê de um projeto gerado em segundos (sem meta específica)

**Constraints**: só dados de versões aprovadas; dossiê final só sem item obrigatório faltando;
nada de texto regulatório inventado (estrutura e títulos do contexto; declaração do RT/RL com o
texto do contexto); os modelos de `docs/modelos` não são lidos

**Scale/Scope**: um dossiê por projeto ou família, poucas versões por ano

## Constitution Check

| Princípio | Como o plano atende | Situação |
| --- | --- | --- |
| I. Rastreabilidade | Cada versão do dossiê guarda definição, textos padrão e versões de origem usados | Atende |
| II. Trilha imutável | Checagem, geração, complementos, textos, envio, resultado e aditamento geram eventos; versões somente de inclusão | Atende |
| III. Assinatura | Aprovação de texto padrão com reautenticação (005); PDF assinado do RT/RL arquivado no envio | Atende |
| IV. Modelos versionados | Definição do dossiê e textos padrão versionados | Atende |
| V. Fonte única | Itens montados do conteúdo congelado dos subdocumentos, dos estudos, das normas e referências do cadastro | Atende |
| VI. Cálculo automático | Resultados dos estudos como calculados na 007 | Atende |
| VII. Segurança | Gerar, complementar e registrar envio: Qualidade/AR; consultar: acesso ao projeto | Atende |
| VIII. Qualidade verificável | Testes de checagem por classe, árvore de títulos, bloqueio do final e aditamento | Atende |
| IX. Simplicidade | Definição declarativa e um montador de conteúdo comum ao PDF e ao DOCX | Atende |

## Project Structure

```text
specs/011-dossie-tecnico/  plan.md, research.md, data-model.md, quickstart.md, contracts/, tasks.md
sgp/dossier/
├── definicao_padrao.yaml   # estrutura I a XII, classes e fontes (semente da definição)
├── definition.py   # leitura e validação da definição
├── sources.py      # conteúdo de cada fonte (subdocumento, estudos, normas, referências, anexos, textos, complementos)
├── check.py        # classe, família e checagem item a item
├── render.py       # HTML (PDF/A) e DOCX no formato do dossiê
├── diff.py         # comparação por item para o aditamento
├── models.py       # DossierDefinition, StandardText, CompanyProfile, DossierSupplement, DossierVersion, Submission
├── services.py / views.py / urls.py / event_types.py / templates/dossier/
tests/dossier/
```

## Complexity Tracking

Sem violações da constituição a justificar.
