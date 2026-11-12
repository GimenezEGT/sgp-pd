# Evidências de validação Checklist: Cópia de segurança, restauração e qualificação do sistema

**Purpose**: Avaliar se os requisitos de qualificação de instalação e de operação, relatórios, revisão de acessos e roteiros produzem evidência suficiente para a validação do sistema (revisão de requisitos, não de código)
**Created**: 2026-11-12
**Feature**: [spec.md](../spec.md)

**Review Ownership**: This checklist is a reviewer-owned requirements-quality review artifact. Mark an item `[x]` only when the reviewer determines the requirements-quality criterion is satisfied.

Profundidade: padrão. Público: Garantia da Qualidade e TI.

## Requirement Completeness

- [ ] CHK001 Os itens conferidos na qualificação de instalação estão listados com critério de aprovação verificável? [Completeness, Spec §FR-011]
- [ ] CHK002 Os itens da qualificação de operação estão listados, com a garantia explícita de não alterar dados? [Completeness, Spec §FR-012]
- [ ] CHK003 O conteúdo mínimo do relatório (data, executor, versão do sistema, resultado por item, resultado geral) está definido? [Completeness, Spec §FR-011, §FR-013]
- [ ] CHK004 Está definido como a suíte automatizada da mesma versão entra na evidência da qualificação de operação? [Completeness, Spec §FR-012, §US4]
- [ ] CHK005 Os roteiros manuais dos fluxos críticos (assinatura, auditoria, geração) têm campos para resultado obtido, executor, data e evidência? [Completeness, Spec §FR-015]
- [ ] CHK006 As colunas da exportação da revisão de acessos estão especificadas? [Completeness, Spec §FR-014]

## Requirement Clarity

- [ ] CHK007 Os possíveis resultados de um item (aprovado, reprovado, não aplicável) e a regra do resultado geral estão definidos? [Clarity, Spec §FR-011]
- [ ] CHK008 "Versão do sistema" está definida de forma que ligue cada evidência a uma versão do repositório? [Clarity, Spec §FR-011, §FR-013]
- [ ] CHK009 Está claro quem pode executar cada qualificação e por qual canal (linha de comando ou tela)? [Clarity, Spec §FR-011, §FR-012, §Clarifications]

## Requirement Consistency

- [ ] CHK010 As permissões de execução e de consulta das qualificações são coerentes entre spec, contrato de rotas e roteiros? [Consistency, Spec §FR-011, §FR-012, §FR-013]
- [ ] CHK011 Os entregáveis do plano (especificações, matriz, IQ, OQ, PQ, relatório de validação) estão mapeados para onde estão ou para quem os produz? [Consistency, Spec §Assumptions]

## Scenario Coverage

- [ ] CHK012 Está definido o resultado da qualificação quando um serviço externo (diretório, e-mail, Sankhya) não está configurado no ambiente? [Coverage, Gap]
- [ ] CHK013 A revalidação periódica (repetição de IQ e OQ) mantém o histórico das execuções anteriores? [Coverage, Spec §FR-013]
- [ ] CHK014 Está definido o tratamento de uma qualificação reprovada (registro, continuidade, nova execução)? [Coverage, Gap]

## Non-Functional Requirements

- [ ] CHK015 Está explícito que a qualificação não expõe valores de segredos no relatório? [Security, Spec §FR-011]
- [ ] CHK016 A integridade do relatório guardado (resumo SHA-256, imutabilidade da execução) está especificada? [Integrity, Spec §FR-013]
- [ ] CHK017 Cada execução, exportação e download de relatório gera evento na trilha? [Traceability, Spec §FR-013, §FR-014]

## Acceptance Criteria Quality

- [ ] CHK018 SC-003 define quais configurações inválidas devem reprovar a qualificação de instalação? [Measurability, Spec §SC-003]
- [ ] CHK019 SC-004 identifica quem assina os roteiros manuais e onde a evidência fica registrada? [Measurability, Spec §SC-004]

## Dependencies & Assumptions

- [ ] CHK020 Está registrado que plano, relatório de validação e qualificação de desempenho são da Garantia da Qualidade? [Assumption, Spec §Assumptions]
