# Implementation Plan: Estudos de desempenho e estabilidade com cálculo automático

**Branch**: `007-estudos-calculo` | **Date**: 2026-11-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/007-estudos-calculo/spec.md`

## Summary

Estudos do projeto com tipo controlado, critério congelado, medidas lançadas ou importadas
(CSV/XLSX com mapeamento por equipamento) e cálculo automático (descritivas, diferenças, regressão,
correlação, proporções com IC 95%, detecção e desvios) com regra de arredondamento registrada;
"não aplicável" com justificativa; vínculo ao tópico do RAPD ou da Validação, entrando no conteúdo
assinado (005) e no documento gerado (006); bloqueio na aprovação e nova versão com motivo.

Abordagem técnica (entrada do `/speckit-plan`): app "estudos" com Estudo, Critério, Medida e
Resultado (critérios, medidas e resultados como dados estruturados do estudo); cálculos num módulo
Python puro com SciPy/NumPy; desvio amostral (n − 1); IC pelo método do esclarecimento; arredondamento
configurável; importação com mapeamento salvo; testes com os vetores de referência e `hypothesis`;
tabelas pelo gerador da 006.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: as anteriores, mais SciPy (com NumPy) no runtime e hypothesis nos testes

**Storage**: PostgreSQL 17 (estudo com linhas e resultados em JSONB; versões por linhagem)

**Testing**: pytest + hypothesis; vetores V1–V8; marcador `req("007:…")`

**Target Platform / Project Type**: os mesmos; aplicação web monolítica

**Performance Goals**: 500 medidas calculadas em < 2 s; pré-visualização de 1.000 linhas em < 10 s

**Constraints**: nenhum campo para valor calculado; estudo bloqueado não muda; resultados com vírgula
decimal e regra registrada

**Scale/Scope**: dezenas de estudos por projeto, até milhares de medidas por estudo

## Constitution Check

| Princípio | Como o plano atende | Situação |
| --- | --- | --- |
| I. Rastreabilidade | Versões por linhagem com motivo; gravações e importações na trilha | Atende |
| II. Trilha imutável | Criação, gravação, critério, importação, não aplicável, bloqueio e versão geram eventos | Atende |
| III. Assinatura | Conteúdo dos estudos entra no resumo assinado do subdocumento | Atende |
| IV. Modelos versionados | Tipos de estudo são lista controlada; modelos de formulário não mudam | Atende |
| V. Fonte única | Linhas referenciam amostras, lotes e kits por id da versão do cadastro | Atende |
| VI. Cálculo automático | Nenhum campo para média, DP, CV% etc.; vetores de referência em teste | Atende |
| VII. Segurança | Edição pelos editores do projeto; consulta por acesso ao projeto; negação registrada | Atende |
| VIII. Qualidade verificável | TDD no módulo de cálculo (vetores e propriedades) e nas regras | Atende |
| IX. Simplicidade | Um módulo de cálculo puro e perfis declarativos; sem tabelas de linhas | Atende |

## Project Structure

```text
specs/007-estudos-calculo/  plan.md, research.md, data-model.md, quickstart.md, contracts/, tasks.md
sgp/studies/
├── stats.py        # cálculo puro e arredondamento (sem Django)
├── profiles.py     # perfis por tipo de estudo: colunas, métricas e critérios
├── models.py       # Study, ImportMapping
├── services.py     # criar, gravar linhas, critérios, não aplicável, importar, bloquear, nova versão
├── importing.py    # CSV/XLSX, mapeamento e pré-visualização
└── views.py / forms.py / urls.py / event_types.py / templates/studies/
sgp/vocab/migrations/0005_seed_estudos.py
sgp/signatures/documents.py, sgp/subdocuments/services.py, sgp/documents/content.py  # integração
tests/studies/
```

## Complexity Tracking

Sem violações da constituição a justificar.
