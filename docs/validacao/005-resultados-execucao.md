# Feature 005 — resultados de execução (evidência)

Ambiente de desenvolvimento, 2026-11-07, dados fictícios. Senhas do LDAP de desenvolvimento.

## Suíte automatizada

| Item | Resultado |
| --- | --- |
| Testes (`pytest`) | 741 aprovados (todas as features até a 005), 0 falhas |
| Cobertura `sgp/core` / `sgp/audit` | 93,5% / 97,1% |
| Matriz de rastreabilidade | 131 requisitos (001 a 005), 0 sem cobertura |
| SC-001 adulteração da versão aprovada | apontada pela verificação |
| SC-004 terceira falha de senha | bloqueio e alerta |
| SC-005 verificação de 10 versões | abaixo de 2 s |

## Roteiro do quickstart na pilha real (Nginx HTTPS → Django → OpenLDAP → PostgreSQL)

| Cenário | Resultado |
| --- | --- |
| `ana.analista` envia a Formulação: senha errada recusada; com a senha certa fica "Em revisão" com a assinatura "Elaborado" | aprovado |
| Edição em revisão recusada | aprovado |
| `gestor.pd` devolve: sem comentário recusado, com comentário devolvido; `ana.analista` corrige e reenvia (assina de novo) | aprovado |
| `ana.analista` não abre a aprovação (403); `gestor.pd` aprova com a senha | aprovado |
| Alteração direta no banco do conteúdo congelado: a verificação aponta resumo divergente e conteúdo atual diferente | aprovado |
| Nova versão: sem motivo recusada; com motivo nasce a 02 e a 01 aparece "Substituída" | aprovado |
| Três senhas erradas seguidas: assinatura bloqueada; a senha certa também é recusada até o fim do bloqueio; alerta na trilha | aprovado |
| Projeto novo submetido e aprovado com as senhas do líder e do Gestor: `PD-2026-002`, TAP e Plano com "Elaborado" e "Aprovado"; verificação do TAP íntegra | aprovado |

Defeito encontrado e corrigido no roteiro: depois de uma devolução, a verificação apontava como
divergente a assinatura "Elaborado" da primeira rodada. A regra passou a exigir uma assinatura
"Elaborado" e a "Aprovado" sobre o conteúdo aprovado; as rodadas anteriores ficam como histórico
(teste automatizado acrescentado).

## Pendências que dependem de terceiros

- Ratificar com a Garantia da Qualidade: significados e obrigatoriedade, delegação (perfis e
  prazo), assinatura opcional da Qualidade e o procedimento (PSG 20 ou POP) que declara a
  equivalência da assinatura eletrônica à manuscrita.
- Ratificar com a TI o tempo de bloqueio e com o Gestor de P&D o prazo de revisão.
- Projetos e subdocumentos aprovados antes da 005 (aprovação provisória) não têm versão congelada;
  ganham versões a partir da próxima aprovação.
