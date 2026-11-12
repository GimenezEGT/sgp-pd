# Feature 013 — resultados de execução (evidência)

Ambiente de desenvolvimento, 2026-11-11, dados fictícios. Senhas do LDAP de desenvolvimento.
Feature pedida pelo usuário em 2026-11-07 (fora do roteiro original do plano).

## Suíte automatizada

| Item | Resultado |
| --- | --- |
| Testes (`pytest`) | 909 aprovados (todas as features até a 013, com a convergência), 0 falhas |
| Cobertura `sgp/core` / `sgp/audit` | 93,5% / 97,1% |
| Matriz de rastreabilidade | 188 requisitos (001 a 006 e 013), 0 sem cobertura |
| SC-001 perfis | nenhuma pessoa sem o perfil exigido abre, envia, aprova ou descarta revisão, nem pela URL (testes e varredura de rotas) |
| SC-002 documentos iniciados | ficam na versão em que começaram depois da publicação |
| SC-003 adulteração | alteração direta no banco de versão publicada apontada pela verificação |
| SC-004 histórico | etapas, pessoas, datas, motivo, impacto, comentários e documentos por versão |

## Roteiro do quickstart na pilha real (Nginx HTTPS → Django → OpenLDAP → PostgreSQL)

| Cenário | Resultado |
| --- | --- |
| Migração: campos de revisão nas tabelas de modelos e resumo de base gravado nas versões já publicadas (Entrada 05 e layouts) | aprovado |
| `qualidade.ar` abre a versão 06 da Entrada, altera o rótulo do tópico 13 e envia: sem motivo e impacto recusado; com motivo e impacto enviado; revisão sem mudança recusada ("não muda nada") | aprovado |
| `ana.analista` abre a aprovação: 403; `gestor.pd` vê a comparação (1 alteração) e devolve com comentário; `qualidade.ar` reenvia | aprovado |
| `qualidade.ar` tenta aprovar: 403; `gestor.pd` aprova com a senha de rede e vigência imediata: 06 vigente, 05 substituída, resumo aprovado gravado | aprovado |
| Histórico: revisão aberta, enviada, devolvida, aprovada com assinatura e em vigência; comparação 05 × 06 | aprovado |
| Verificação de integridade da 06: íntegra | aprovado |
| Layout do TAP: versão 02 aprovada com vigência em 7 dias; a 01 continua vigente; nova revisão recusada até a data | aprovado |
| Retirada de uso da Alteração de Projeto pedida pela Qualidade e devolvida pelo Gestor com comentário (a aprovação com assinatura e o bloqueio de novos documentos estão nos testes automatizados) | aprovado |
| Trilha: `templates.submitted`, `returned`, `approved`, `became_current`, `verified`, `retirement_requested`, `retirement_returned` e publicações | aprovado |

O ciclo completo pelo roteiro levou 6 s; o SC-005 (menos de 5 minutos para quem conhece a tela) fica
registrado como verificação manual a repetir na homologação.

## Pendências a ratificar

- Perfis do ciclo (Qualidade/AR elabora; Gestor de P&D aprova), vigência futura, retirada com
  aprovação e assinatura só na aprovação: respostas provisórias de 2026-11-07.
- Layout não é retirado de uso (troca por nova versão): resposta provisória de 2026-11-11.
- Resumo de base das versões publicadas antes da 013: gravado na implantação; conferir com a
  Garantia da Qualidade se essas versões precisam de aprovação retroativa.
