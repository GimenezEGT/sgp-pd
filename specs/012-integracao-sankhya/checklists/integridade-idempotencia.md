# Integridade e idempotência Checklist: Integração com o Sankhya

**Purpose**: Avaliar se os requisitos garantem envio único, rastreável e sem perda (revisão de requisitos, não de código)
**Created**: 2026-11-12
**Feature**: [spec.md](../spec.md)

**Review Ownership**: This checklist is a reviewer-owned requirements-quality review artifact. Mark an item `[x]` only when the reviewer determines the requirements-quality criterion is satisfied.

Profundidade: padrão. Público: TI e Garantia da Qualidade.

- [ ] CHK001 A mensagem nasce na mesma transação da aprovação (nada se perde se o envio falhar)? [Completeness, Spec §FR-004]
- [ ] CHK002 A chave de idempotência e a regra de reenvio garantem um único registro no ERP? [Measurability, Spec §FR-005, SC-001]
- [ ] CHK003 As novas tentativas têm limite e espera definidos, e a falha fica visível? [Clarity, Spec §FR-005, §FR-007]
- [ ] CHK004 A falha de integração nunca bloqueia o trabalho no sistema? [Completeness, Spec §FR-009, SC-004]
- [ ] CHK005 A exportação de contingência tem layout definido e reproduz os registros da fila? [Measurability, Spec §FR-008, SC-003]
- [ ] CHK006 A mudança de mapeamento mantém as mensagens antigas reprocessáveis? [Coverage, Spec §Edge Cases]
