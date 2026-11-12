# Pacote de validação do SGP-P&D

O SGP-P&D guarda registros de controle de projeto e precisa ser validado antes do uso oficial
(RDC 665/2022, arts. 104 a 106; seção "Validação do sistema computadorizado e implantação" de
[docs/plano-implementacao.md](../plano-implementacao.md)). Este índice liga cada entregável de
validação do plano ao lugar em que está no repositório ou a quem o produz.

| Entregável | Onde está | Situação |
| --- | --- | --- |
| Plano de validação (escopo, abordagem por risco, responsáveis) | Garantia da Qualidade (Fase 0) | Pendente — responsabilidade da Garantia da Qualidade |
| Especificação de requisitos do usuário | `specs/*/spec.md` (requisitos FR e critérios SC numerados, cenários de aceitação) | Entregue (features 001 a 014); decisões provisórias marcadas "ratificar com …" |
| Especificação funcional e de projeto | `specs/*/plan.md`, `data-model.md`, `contracts/` | Entregue |
| Análise de risco do sistema | Checklists de `specs/*/checklists/` e análises (`/speckit-analyze`) registradas nos commits | Checklists de requisitos aguardam a revisão (marcação) das pessoas indicadas em cada um |
| Matriz de rastreabilidade requisito → teste | [matriz-rastreabilidade.md](matriz-rastreabilidade.md), gerada por `scripts/rastreabilidade.py` no portão `scripts/verificar.sh` | Gerada a cada execução do portão |
| Verificações manuais (requisitos sem teste automatizado) | [verificacoes-manuais.json](verificacoes-manuais.json) | A executar em homologação |
| Qualificação de instalação (IQ) | [iq-roteiro.md](iq-roteiro.md) + `python manage.py qualificacao_instalacao` (relatório PDF guardado no sistema) | A executar no servidor de homologação e de produção |
| Qualificação de operação (OQ) | [oq-roteiro.md](oq-roteiro.md): suíte automatizada, `python manage.py qualificacao_operacao` e roteiros manuais de assinatura, auditoria e geração | A executar em homologação |
| Qualificação de desempenho (PQ) | Piloto com projeto real em paralelo (plano, "Implantação", passo 3) | Pendente — Gestor de P&D e Garantia da Qualidade |
| Relatório de validação e liberação | Garantia da Qualidade | Pendente |
| Controle de mudanças | Cada mudança passa pelo ciclo do spec-kit (`specs/NNN-*`), com avaliação de impacto na validação (art. 106) e nova execução da OQ | Em uso desde a feature 001 |
| Cópia de segurança e teste de restauração (art. 35) | Feature 014: cópia diária, teste de restauração mensal e painel "Operação e validação"; procedimento de recuperação em [../operacao/recuperacao.md](../operacao/recuperacao.md) | Entregue; destino definitivo a montar pela TI |
| Evidências de execução por feature | `docs/validacao/NNN-resultados-execucao.md` | Ambiente de desenvolvimento, dados fictícios |

## Operação depois da liberação (plano, "Implantação", passo 7)

- Cópia diária às 01:00 e teste de restauração mensal (dia 1, 03:00), com aviso por e-mail à TI em
  caso de falha ou de cópia atrasada (mais de 26 horas).
- Revisão trimestral de acessos: exportação em "Operação e validação" → "Revisão periódica de
  acessos" (CSV ou XLSX), conferida pela TI e pela Garantia da Qualidade.
- Revalidação periódica (art. 105) e depois de cada mudança: repetir a OQ (e a IQ quando mudar a
  instalação); o histórico das execuções fica no painel, com os relatórios guardados.
