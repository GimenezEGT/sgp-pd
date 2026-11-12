# Estatística (fórmulas e arredondamento) Checklist: Estudos com cálculo automático

**Purpose**: Avaliar se os requisitos de cálculo são completos, inequívocos e verificáveis (revisão de requisitos, não de código)
**Created**: 2026-11-11
**Feature**: [spec.md](../spec.md)

**Review Ownership**: This checklist is a reviewer-owned requirements-quality review artifact. Mark an item `[x]` only when the reviewer determines the requirements-quality criterion is satisfied.

Profundidade: padrão. Público: Garantia da Qualidade e P&D.

- [ ] CHK001 Está definido o desvio-padrão amostral (n − 1) e quando o populacional aparece? [Clarity, Spec §FR-007]
- [ ] CHK002 Cada tipo de estudo tem as métricas calculadas e as aceitas no critério definidas? [Completeness, contracts/perfis-calculo.md]
- [ ] CHK003 O método do IC 95% e a opção alternativa estão definidos, com vetor de referência para cada um? [Clarity, Spec §Clarifications, §SC-001]
- [ ] CHK004 A regra de arredondamento, as casas por tipo de resultado e o momento do arredondamento (só na exibição) estão definidos? [Clarity, Spec §FR-004, §FR-011]
- [ ] CHK005 Todos os casos "não calculáveis" estão listados (média zero, uma medida, x constante, proporção sem casos)? [Coverage, Spec §FR-010, Edge Cases]
- [ ] CHK006 Está definido como critério com grupos (por dia, por lote) é avaliado? [Clarity, contracts/perfis-calculo.md]
- [ ] CHK007 A regressão define a variável dependente e a independente em cada tipo? [Clarity, contracts/perfis-calculo.md]
- [ ] CHK008 O desempenho exigido (500 medidas, 1.000 linhas importadas) é mensurável? [Measurability, Spec §SC-004, §SC-005]
