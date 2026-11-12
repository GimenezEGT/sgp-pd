# Integridade de dados (ALCOA+) Checklist: Caderno de laboratório eletrônico

**Purpose**: Avaliar se os requisitos garantem registros atribuíveis, legíveis, contemporâneos, originais e exatos, completos, consistentes, duradouros e disponíveis (revisão de requisitos, não de código)
**Created**: 2026-11-11
**Feature**: [spec.md](../spec.md)

**Review Ownership**: This checklist is a reviewer-owned requirements-quality review artifact. Mark an item `[x]` only when the reviewer determines the requirements-quality criterion is satisfied.

Profundidade: padrão. Público: Garantia da Qualidade.

- [ ] CHK001 Toda entrada, adendo, anexo, material e vínculo identifica quem registrou e quando (atribuível)? [Completeness, Spec §FR-001, §FR-007, §FR-010]
- [ ] CHK002 A data e a hora vêm só do servidor, sem campo de data editável pelo pesquisador (contemporâneo)? [Clarity, Spec §FR-001]
- [ ] CHK003 O registro original permanece inalterado depois da assinatura e a correção fica em adendo separado, datado e assinado (original)? [Completeness, Spec §FR-007, SC-001]
- [ ] CHK004 A assinatura cobre um resumo do conteúdo que permita detectar alteração posterior (exato)? [Measurability, Spec §FR-006]
- [ ] CHK005 Os anexos têm resumo criptográfico conferido em cada leitura (exato, duradouro)? [Completeness, Spec §FR-003]
- [ ] CHK006 Os materiais apontam a versão do cadastro usada, e não só um texto livre (consistente)? [Clarity, Spec §FR-002]
- [ ] CHK007 Vínculos e retiradas são lógicos, com quem e quando, sem apagar nada (completo)? [Completeness, Spec §FR-010]
- [ ] CHK008 A promoção para estudo registra a origem dos dados nos dois sentidos (rastreável)? [Completeness, Spec §FR-011, SC-003]
- [ ] CHK009 O texto formatado é legível na tela e preserva o conteúdo informado, sem perder tabelas e imagens coladas (legível)? [Clarity, Spec §FR-001, Plan §R1, §R2]
- [ ] CHK010 Os eventos de criação, alteração, anexo, assinatura, testemunho, adendo, vínculo e promoção estão todos na trilha (disponível)? [Coverage, Spec §FR-014]
- [ ] CHK011 O prazo de assinatura e o tratamento de entrada atrasada estão definidos e mensuráveis? [Measurability, Spec §FR-008, §Clarifications]
- [ ] CHK012 Os critérios de testemunha (quando é obrigatória e quem pode ser) estão definidos sem ambiguidade? [Clarity, Spec §FR-009, §Clarifications]
- [ ] CHK013 O modelo de entrada usado (e a versão) fica registrado e não altera entradas antigas? [Consistency, Spec §FR-005, US2]
- [ ] CHK014 A guarda e a retenção dos registros do caderno estão definidas ou remetidas à política de backup? [Gap]
