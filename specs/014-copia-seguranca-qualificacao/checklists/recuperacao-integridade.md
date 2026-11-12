# Recuperação e integridade das cópias Checklist: Cópia de segurança, restauração e qualificação do sistema

**Purpose**: Avaliar se os requisitos de cópia, retenção, teste de restauração e avisos garantem a recuperação íntegra dos registros (revisão de requisitos, não de código)
**Created**: 2026-11-12
**Feature**: [spec.md](../spec.md)

**Review Ownership**: This checklist is a reviewer-owned requirements-quality review artifact. Mark an item `[x]` only when the reviewer determines the requirements-quality criterion is satisfied.

Profundidade: padrão. Público: TI e Garantia da Qualidade.

## Requirement Completeness

- [ ] CHK001 Está explícito que a cópia abrange o banco e todos os arquivos guardados (anexos, documentos gerados, certificados)? [Completeness, Spec §FR-001]
- [ ] CHK002 O conteúdo mínimo do manifesto (data, versão, resumo e tamanho do banco, contagens, último evento da trilha, lista de arquivos) está especificado? [Completeness, Spec §FR-002]
- [ ] CHK003 Está definido onde fica registrado o resumo do próprio manifesto, para detectar troca do manifesto? [Completeness, Spec §FR-002]
- [ ] CHK004 As conferências do teste de restauração estão listadas uma a uma, com o critério de aprovação de cada uma? [Completeness, Spec §FR-006]
- [ ] CHK005 O destino das cópias e a responsabilidade pela segunda cópia fora do prédio estão definidos? [Completeness, Spec §FR-003, §Clarifications]

## Requirement Clarity

- [ ] CHK006 "Ponto consistente no tempo" está definido de forma verificável (o manifesto e o banco copiado descrevem o mesmo instante)? [Clarity, Spec §FR-001]
- [ ] CHK007 A regra de retenção define sem ambiguidade qual cópia é "a primeira bem-sucedida de cada mês" e o que acontece com o registro de uma cópia removida? [Clarity, Spec §FR-005]
- [ ] CHK008 "Destino igual ao diretório dos dados" cobre também destino dentro do diretório dos dados? [Ambiguity, Spec §FR-003]

## Requirement Consistency

- [ ] CHK009 A remoção de cópias diárias pela retenção é coerente com a regra "nada é apagado fisicamente" da constituição (cópias não são registros do sistema; arquivos do acervo nunca são removidos)? [Consistency, Spec §FR-005]
- [ ] CHK010 A frequência mensal do teste de restauração é a mesma no spec, no plano de implementação e no roteiro de operação? [Consistency, Spec §FR-006]

## Scenario & Edge Case Coverage

- [ ] CHK011 Estão especificados os cenários de destino indisponível, sem espaço ou sem permissão de gravação? [Coverage, Spec §FR-003, §Edge Cases]
- [ ] CHK012 Está definido o comportamento quando um arquivo guardado falta no armazenamento na hora da cópia? [Edge Case, Spec §Edge Cases]
- [ ] CHK013 Estão cobertos os danos possíveis à cópia (manifesto, banco copiado, arquivo do acervo alterado ou ausente) no teste de restauração? [Coverage, Spec §SC-002]
- [ ] CHK014 Está definido o que acontece com o banco isolado de um teste interrompido? [Edge Case, Spec §Edge Cases]
- [ ] CHK015 Está definido o comportamento de pedidos simultâneos de cópia ou de teste? [Coverage, Spec §Edge Cases]
- [ ] CHK016 A recuperação real (restaurar sobre o banco em uso) tem procedimento documentado e fica fora da interface? [Coverage, Spec §FR-009, §FR-015]

## Non-Functional Requirements

- [ ] CHK017 Está explícito que a cópia não interrompe o uso do sistema? [Non-Functional, Spec §FR-001]
- [ ] CHK018 A proteção do conteúdo das cópias (acesso ao destino, cifragem, ausência de download pela tela) está especificada? [Security, Spec §FR-010]
- [ ] CHK019 Os destinatários, o gatilho (falha e atraso de 26 horas) e o conteúdo dos avisos estão definidos? [Completeness, Spec §FR-008]

## Acceptance Criteria Quality

- [ ] CHK020 SC-001 e SC-002 são mensuráveis por teste automatizado com cópia real e dano provocado? [Measurability, Spec §SC-001, §SC-002]

## Dependencies & Assumptions

- [ ] CHK021 A dependência de infraestrutura (servidor de destino, cifragem do armazenamento, e-mail) está registrada como responsabilidade da TI? [Assumption, Spec §Assumptions]
- [ ] CHK022 A premissa de que o teste usa o mesmo servidor de banco, num banco isolado, está registrada e aceita? [Assumption, Spec §Assumptions]
