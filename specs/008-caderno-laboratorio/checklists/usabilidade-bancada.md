# Usabilidade em bancada Checklist: Caderno de laboratório eletrônico

**Purpose**: Avaliar se os requisitos tornam o registro rápido e confiável durante o trabalho de laboratório (revisão de requisitos, não de código)
**Created**: 2026-11-11
**Feature**: [spec.md](../spec.md)

**Review Ownership**: This checklist is a reviewer-owned requirements-quality review artifact. Mark an item `[x]` only when the reviewer determines the requirements-quality criterion is satisfied.

Profundidade: padrão. Público: pesquisadores do grupo piloto e Gestor de P&D.

- [ ] CHK001 Criar uma entrada exige poucos campos no início (título, modelo, relevância) e permite completar depois? [Clarity, Spec §US1, Plan §R3]
- [ ] CHK002 Os modelos de entrada reduzem a digitação para os tipos de experimento mais comuns? [Coverage, Spec §US2, §FR-005]
- [ ] CHK003 Foto e arquivo de equipamento entram sem passos extras (colar, arrastar ou enviar)? [Completeness, Spec §FR-003, Plan §R3]
- [ ] CHK004 Materiais são informados pelo código impresso no rótulo, com recusa clara de código inexistente? [Clarity, Spec §FR-002]
- [ ] CHK005 As mensagens de recusa (anexo grande, tipo não aceito, senha errada, entrada bloqueada) dizem o motivo e o que fazer? [Clarity, Spec §Edge Cases]
- [ ] CHK006 A situação de cada entrada (aberta, atrasada, assinada, aguardando testemunha, testemunhada) é visível na linha do tempo? [Completeness, Spec §FR-012]
- [ ] CHK007 A busca aceita palavras sem acento e códigos de lote e amostra? [Coverage, Spec §FR-013, Plan §R10]
- [ ] CHK008 O tempo de resposta da busca está definido para o volume esperado? [Measurability, SC-004]
- [ ] CHK009 O uso em tela pequena (tablet na bancada) está previsto ou registrado como fora do escopo? [Gap]
- [ ] CHK010 O comportamento sem rede ou com sessão expirada durante o registro (perda de texto) está tratado? [Gap]
