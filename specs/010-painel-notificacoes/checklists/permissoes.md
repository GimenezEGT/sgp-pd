# Permissões Checklist: Painel do gestor e notificações

**Purpose**: Avaliar se os requisitos garantem que cada pessoa veja e receba só o que pode (revisão de requisitos, não de código)
**Created**: 2026-11-11
**Feature**: [spec.md](../spec.md)

**Review Ownership**: This checklist is a reviewer-owned requirements-quality review artifact. Mark an item `[x]` only when the reviewer determines the requirements-quality criterion is satisfied.

Profundidade: padrão. Público: TI, Garantia da Qualidade e Gestor de P&D.

- [ ] CHK001 Está definido que o painel só lista projetos pela regra única de acesso? [Clarity, Spec §FR-001]
- [ ] CHK002 Custo e retorno estão protegidos no painel, na planilha e nos e-mails? [Completeness, Spec §FR-002, §FR-006, SC-003]
- [ ] CHK003 A linha do tempo exige acesso ao projeto e não expõe valores da trilha restritos à Qualidade? [Gap, Spec §FR-003]
- [ ] CHK004 A fila do gestor considera delegações ativas e exclui documentos de projetos sem acesso? [Coverage, Spec §FR-004]
- [ ] CHK005 Está definido quem recebe cada tipo de e-mail e que o e-mail não leva dados restritos? [Completeness, Spec §FR-007, contracts/notificacoes.md]
- [ ] CHK006 A regra de que assinatura pendente não pode ser desligada está explícita e testável? [Clarity, Spec §FR-008]
- [ ] CHK007 Exportação e mudanças de preferência ficam na trilha? [Completeness, Spec §FR-006, §FR-009]
