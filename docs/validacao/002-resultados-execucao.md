# Feature 002 — resultados de execução (evidência)

Ambiente de desenvolvimento, 2026-11-07, dados fictícios.

## Suíte automatizada

| Item | Resultado |
| --- | --- |
| Testes (`pytest`) | 370 aprovados (todas as features até a 002), 0 falhas |
| Cobertura `sgp/core` / `sgp/audit` | 93,5% / 97,1% |
| Matriz de rastreabilidade | 59 requisitos (001 e 002), 0 sem cobertura |
| SC-003 aprovações simultâneas | 6 aprovações em paralelo → `PD-AAAA-001` a `006`, sem repetição |
| SC-005 lista de 200 projetos | abaixo de 2 s |

## Roteiro do quickstart na pilha real (Nginx HTTPS → Django → OpenLDAP → PostgreSQL)

| Cenário | Resultado |
| --- | --- |
| `lider.projeto` cria o projeto (ANVISA, classe II), preenche TAP, marco e Plano de Negócios em formato BR (987.654,32) | aprovado |
| `ana.analista` incluída na equipe não abre o projeto antes da aprovação (403) | aprovado |
| Submissão, devolução com comentário pelo `gestor.pd`, ressubmissão e aprovação | aprovado |
| Código `PD-2026-001`, versão 01, situação Aberto | aprovado |
| Gestor de P&D vê R$ 987.654,32 | aprovado |
| `ana.analista`, depois da aprovação, abre o projeto e vê "Restrito"; valor não aparece; edição do plano dá 403 | aprovado |
| `qualidade.ar`: edição do plano 403; trilha mostra `[restrito]` e não o valor | aprovado |

## Pendências que dependem de terceiros

- Ratificar com o Gestor de P&D: campos do TAP, formato do código, significado do retorno,
  ausência de alçada por custo e perfis com acesso financeiro.
