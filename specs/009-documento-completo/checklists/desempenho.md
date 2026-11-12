# Desempenho Checklist: Documento completo do projeto

**Purpose**: Avaliar se os requisitos de tempo, volume e comportamento sob carga estão definidos e mensuráveis (revisão de requisitos, não de código)
**Created**: 2026-11-11
**Feature**: [spec.md](../spec.md)

**Review Ownership**: This checklist is a reviewer-owned requirements-quality review artifact. Mark an item `[x]` only when the reviewer determines the requirements-quality criterion is satisfied.

Profundidade: padrão. Público: TI e Gestor de P&D.

- [ ] CHK001 A meta de tempo (300 páginas em menos de 3 minutos) define o ambiente de medição (servidor de homologação)? [Measurability, Spec §SC-003]
- [ ] CHK002 O comportamento durante a geração (assíncrona, progresso visível, aviso ao terminar) está especificado? [Completeness, Spec §FR-006]
- [ ] CHK003 Está definido o que acontece com pedidos simultâneos do mesmo projeto? [Gap, Plan §data-model]
- [ ] CHK004 O reaproveitamento sem mudanças está definido com o critério de "nada mudou"? [Clarity, Spec §Edge Cases, Plan §R10]
- [ ] CHK005 O tratamento de falha (mensagem, registro e nova tentativa) está especificado? [Completeness, Spec §Edge Cases, §FR-015]
- [ ] CHK006 Limites de volume (número de entradas do caderno, imagens e anexos) e o efeito no tempo estão estimados? [Gap]
