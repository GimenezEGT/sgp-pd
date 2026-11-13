# Feature 015 — resultados de execução (evidência)

Ambiente de desenvolvimento, 2026-11-13, dados fictícios. Origem: teste do usuário na pilha local,
em que a Entrada do PD-2026-003 foi enviada para revisão pelo próprio `gestor.pd`, a analista assinou
"Revisado" duas vezes na mesma versão e o Gestor não encontrou como aprovar.

## Suíte automatizada

| Item | Resultado |
| --- | --- |
| Testes (`pytest`) | 1.263 aprovados (todas as features até a 015), 0 falhas |
| Testes da feature (`tests/signatures/test_correcoes_015.py`) | 8 aprovados (antes da correção, 7 falhavam) |
| Matriz de rastreabilidade | 319 requisitos, 0 sem cobertura |
| SC-001 revisão única | segunda assinatura "Revisado" da mesma pessoa na mesma versão recusada com "Você já assinou como revisor esta versão." e sem gravar; a opção some; na versão seguinte a pessoa revisa de novo |
| SC-002 Gestor que elaborou | aviso, link para Delegações e devolução com comentário na tela do documento; devolução sem comentário recusada; seção "Elaborados por você" na Fila de revisão, sem link de aprovação; tela de aprovação sem "Aprovar e assinar" e aprovação pelo endereço direto recusada; delegado que elaborou também não aprova e não vê o link para Delegações; analista que elaborou não vê a devolução |
| SC-003 situação pelo nome | "situação Rascunho" no envio e "situação Em revisão" na aprovação, sem códigos internos |
| Regras da 005 | testes da 005 continuam aprovados (segregação, devolução com comentário, versões, delegação) |

## Conferência na pilha real (somente leitura, sem alterar os dados do teste do usuário)

| Cenário | Resultado |
| --- | --- |
| `gestor.pd` abre a Entrada do PD-2026-003 (enviada por ele): aviso da segregação, link "Delegações de aprovação" e formulário "Devolver"; sem o botão "Aprovar ou devolver" | aprovado |
| Fila de revisão do `gestor.pd`: seção "Elaborados por você — aguardam outro aprovador" com "Entrada de Projeto – versão 01", PD-2026-003, enviada em 13/11/2026 17:56:49, link para o documento e nenhum link de aprovação | aprovado |
| Página de aprovação pelo endereço direto: "situação Em revisão", sem "Aprovar e assinar", com a devolução | aprovado |
| `ana.analista` (que já assinou "Revisado" duas vezes antes da correção): sem o aviso do Gestor e sem a opção de assinar como revisor de novo | aprovado |

As duas assinaturas "Revisado" gravadas antes da correção continuam no registro, como manda a regra
de registros assinados imutáveis. A devolução, o reenvio pela analista e a aprovação pelo Gestor da
Entrada do PD-2026-003 ficam para o usuário fazer no teste dele (o ciclo completo está coberto pelos
testes automatizados).

## Convergência (`/speckit-converge`)

Converged na primeira avaliação: FR-001 a FR-007 e SC-001 a SC-003 implementados e cobertos
por testes (`req("015:…")`); tarefas T001 a T009 concluídas; nenhuma tarefa nova.

## Pendências a ratificar

- Devolução pela própria pessoa que elaborou e tem poder de aprovação — Garantia da Qualidade.
- Envio pelo Gestor de P&D só com aviso (sem bloqueio), com a aprovação por outro Gestor ou por
  delegação — Garantia da Qualidade.
- Checklist `segregacao-assinatura.md` aguarda a revisão (marcação) da Garantia da Qualidade.
