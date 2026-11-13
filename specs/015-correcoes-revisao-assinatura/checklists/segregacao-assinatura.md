# Segregação de funções e assinatura Checklist: Correções do ciclo de revisão e assinatura

**Purpose**: Avaliar se os requisitos da correção preservam a segregação de funções e a integridade das assinaturas (revisão de requisitos, não de código)
**Created**: 2026-11-13
**Feature**: [spec.md](../spec.md)

**Review Ownership**: This checklist is a reviewer-owned requirements-quality review artifact. Mark an item `[x]` only when the reviewer determines the requirements-quality criterion is satisfied.

Profundidade: padrão. Público: Garantia da Qualidade.

## Requirement Completeness

- [ ] CHK001 Está definido que a assinatura "Revisado" é única por pessoa em cada versão, e não por documento? [Completeness, Spec §FR-005]
- [ ] CHK002 Está definido o que acontece com as assinaturas "Revisado" repetidas gravadas antes da correção? [Completeness, Spec §Edge Cases]
- [ ] CHK003 O aviso ao Gestor que elaborou diz o motivo (segregação) e o que fazer (devolver ou delegar)? [Completeness, Spec §FR-001]

## Requirement Clarity

- [ ] CHK004 Está claro quem tem "poder de aprovação" (Gestor de P&D ou delegação vigente) em todos os requisitos? [Clarity, Spec §FR-001, §FR-003, §FR-004]
- [ ] CHK005 Os nomes das situações exibidos estão listados (Rascunho, Em revisão, Devolvido, Aprovado)? [Clarity, Spec §FR-006]

## Requirement Consistency

- [ ] CHK006 A devolução pela própria pessoa que elaborou é coerente com a regra de que quem elaborou não aprova a mesma versão (devolução não aprova)? [Consistency, Spec §FR-002, §FR-007, §Clarifications]
- [ ] CHK007 A delegação continua sem anular a segregação (quem elaborou e tem delegação também não aprova)? [Consistency, Spec §Edge Cases]

## Scenario & Edge Case Coverage

- [ ] CHK008 Está coberto o caso de quem elaborou sem poder de aprovação (analista), que não devolve? [Coverage, Spec §Edge Cases]
- [ ] CHK009 Está coberta a tentativa de aprovar pelo endereço direto da aprovação por quem elaborou? [Coverage, Spec §US1]
- [ ] CHK010 A seção própria da Fila de revisão define as informações mostradas e a ausência de ação de aprovação? [Coverage, Spec §FR-003]

## Acceptance Criteria Quality

- [ ] CHK011 SC-001 e SC-002 são verificáveis por teste automatizado? [Measurability, Spec §SC-001, §SC-002]

## Dependencies & Assumptions

- [ ] CHK012 A ausência de mudança de modelo de dados está registrada e coerente com a recusa no serviço? [Assumption, Spec §Assumptions]
