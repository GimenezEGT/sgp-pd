# Rastreabilidade das versões Checklist: Versionamento do documento final do projeto

**Purpose**: Avaliar se os requisitos tornam rastreáveis as versões do documento final e das partes (revisão de requisitos, não de código)
**Created**: 2026-11-13
**Feature**: [spec.md](../spec.md)

**Review Ownership**: This checklist is a reviewer-owned requirements-quality review artifact. Mark an item `[x]` only when the reviewer determines the requirements-quality criterion is satisfied.

Profundidade: padrão. Público: Garantia da Qualidade.

## Requirement Completeness

- [ ] CHK001 Está definido o que conta como "parte" do documento final (TAP, Plano de Negócios, subdocumentos, Alterações de Projeto)? [Completeness, Spec §Assumptions]
- [ ] CHK002 O conteúdo mínimo de cada versão do documento final (número, data, quem aprovou, mudança, composição, resumo) está listado? [Completeness, Spec §FR-004]
- [ ] CHK003 O histórico de versões de cada parte define as colunas (situação, abertura, motivo, aprovação, versões do documento final)? [Completeness, Spec §FR-008]

## Requirement Clarity

- [ ] CHK004 O gatilho da nova versão (aprovação que faz a parte passar a valer) está definido sem ambiguidade, inclusive o que não gera versão (rascunho, envio, devolução)? [Clarity, Spec §FR-003, §Clarifications]
- [ ] CHK005 Está claro como aprovações simultâneas de mais de uma parte viram uma única versão? [Clarity, Spec §FR-003]
- [ ] CHK006 Os motivos de uma versão (aprovação, recomposição, reconstrução) estão definidos e distinguíveis? [Clarity, Spec §Key Entities, §FR-010]

## Requirement Consistency

- [ ] CHK007 A versão do documento final e a versão do projeto estão separadas de forma coerente em todas as telas e no documento gerado? [Consistency, Spec §FR-002, §FR-007]
- [ ] CHK008 A regra "só versões aprovadas entram no corpo" (feature 009) é coerente com o gatilho da versão? [Consistency, Spec §FR-003]

## Scenario & Edge Case Coverage

- [ ] CHK009 Está definido o comportamento quando a composição vigente não corresponde à última versão registrada (recomposição)? [Edge Case, Spec §FR-010]
- [ ] CHK010 A reconstrução das aprovações anteriores define a ordem, o agrupamento e a marcação das versões? [Coverage, Spec §FR-009]
- [ ] CHK011 Está coberto o projeto sem nenhuma aprovação (documento completo sem versão do documento final)? [Edge Case, Spec §Edge Cases]
- [ ] CHK012 A aprovação de Alteração de Projeto (que muda a versão do projeto) também está coberta na versão do documento final? [Coverage, Spec §Edge Cases]

## Non-Functional Requirements

- [ ] CHK013 A imutabilidade das versões do documento final e o evento na trilha estão exigidos? [Integrity, Spec §FR-004, §FR-005]
- [ ] CHK014 A numeração sem lacuna nem repetição está exigida para aprovações concorrentes? [Integrity, Spec §Edge Cases]

## Acceptance Criteria Quality

- [ ] CHK015 SC-001 e SC-002 são verificáveis por teste automatizado, e SC-003 por conferência na tela? [Measurability, Spec §SC-001 a §SC-003]
