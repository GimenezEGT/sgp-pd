# Segurança de credenciais Checklist: Integração com o Sankhya

**Purpose**: Avaliar se os requisitos protegem credenciais e limitam a integração ao gateway oficial (revisão de requisitos, não de código)
**Created**: 2026-11-12
**Feature**: [spec.md](../spec.md)

**Review Ownership**: This checklist is a reviewer-owned requirements-quality review artifact. Mark an item `[x]` only when the reviewer determines the requirements-quality criterion is satisfied.

Profundidade: padrão. Público: TI e segurança da informação.

- [ ] CHK001 Está explícito que a integração usa só o API Gateway, sem acesso ao banco do ERP? [Clarity, Spec §FR-001]
- [ ] CHK002 Client ID, client secret e X-Token ficam só em variáveis de ambiente e nunca em telas, trilha ou erros registrados? [Completeness, Spec §FR-002]
- [ ] CHK003 O usuário do Sankhya que representa o sistema e as permissões dele estão definidos ou registrados como pendência? [Gap, Spec §Assumptions]
- [ ] CHK004 A renovação do token e o tratamento de token inválido estão especificados? [Coverage, Spec §Edge Cases]
- [ ] CHK005 Quem vê a fila, reprocessa e exporta está restrito e registrado? [Completeness, Spec §FR-007, §FR-009]
- [ ] CHK006 O ambiente de testes da Sankhya é usado antes da produção? [Completeness, Spec §Assumptions]
