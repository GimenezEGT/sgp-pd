# Feature 009 — resultados de execução (evidência)

Ambiente de desenvolvimento, 2026-11-11, dados fictícios. Senhas do LDAP de desenvolvimento.

## Suíte automatizada

| Item | Resultado |
| --- | --- |
| Testes (`pytest`) | 1.091 aprovados (todas as features até a 009 e a 013), 0 falhas; cobertura `sgp/core` 93,5% e `sgp/audit` 97,1%. Depois do gate, o ajuste da mensagem de subdocumento aprovado antes da assinatura eletrônica acrescentou 1 teste, e a pasta `tests/fulldoc` foi rodada de novo |
| Testes da feature (`tests/fulldoc`) | 19 aprovados, mais o de desempenho (`-m slow`) |
| Matriz de rastreabilidade | 248 requisitos, 0 sem cobertura |
| SC-001 sumário | os números do sumário (gerados pela paginação do WeasyPrint) conferem com a página real de cada parte, lida dos marcadores do PDF; "Página X de Y" global |
| SC-002 pendências | tipos do fluxo não criados ou sem versão aprovada, versão sem conteúdo congelado, TAP e Plano sem aprovação assinada e itens da Verificação Final diferentes de "Aprovado" (com a justificativa) aparecem antes de gerar e no rascunho |
| SC-003 desempenho | 588 páginas (projeto completo e 280 entradas do caderno, completo) em 22,0 s no ambiente de desenvolvimento (meta: 300 páginas em menos de 3 min na homologação) |
| SC-004 aprovação pela Qualidade | verificação manual registrada em `docs/validacao/verificacoes-manuais.json` |
| Oficial | sem pendências: PDF/A-2b com selo íntegro (pyHanko), código de verificação no rodapé e reconhecido na tela de verificação da 006 |
| Reaproveitamento | segundo pedido sem mudanças devolve o mesmo documento (`fulldoc.reused`); mudar a opção do caderno gera outro |
| Acesso | gera: líder e Gestor; baixa: quem acessa o projeto, e o documento com dados financeiros só quem tem a permissão; negações registradas |

## Roteiro do quickstart na pilha real

| Cenário | Resultado |
| --- | --- |
| `lider.projeto` abre o documento completo do PD-2026-001: 10 pendências (TAP e Plano aprovados antes da assinatura eletrônica, Entrada aprovada antes da 005, Lote Piloto em rascunho, tipos do fluxo não criados) | aprovado |
| Pedido com o caderno resumido: progresso pela tela (HTMX a cada 2 s: "Gerando 30%"), conclusão pelo worker; rascunho de 11 páginas, com dados financeiros, SHA-256 arquivado | aprovado |
| PDF baixado: sumário cita todas as partes; marcadores na ordem (Pendências p. 3, Formulação v02 p. 4, Quadro de versões p. 6, Resumo da trilha p. 7, Caderno p. 10, Anexos p. 11); marca d'água em todas as páginas; rodapé "Página X de Y" | aprovado |
| Segundo pedido igual: reaproveitado (mesmo documento, evento `fulldoc.reused`) | aprovado |
| `gestor.pd`: caderno completo com histórico de versões e uma versão sem dados financeiros | aprovado |
| `ana.analista` (sem permissão financeira): 403 no documento com dados financeiros, 200 no sem; 403 ao tentar gerar | aprovado |
| `leitor.consulta` sem acesso ao projeto: 403 na tela e no download | aprovado |
| Trilha: `fulldoc.requested` 4, `generated` 3, `reused` 1, `downloaded` 2 | aprovado |

O documento oficial (sem pendências, com selo e código de verificação reconhecido na tela de
verificação) foi exercitado nos testes automatizados com um projeto completo; o banco de
desenvolvimento não tem projeto com todos os subdocumentos aprovados pela assinatura eletrônica.
Ajuste feito depois do roteiro: o subdocumento aprovado antes da assinatura eletrônica aparecia
como "sem versão aprovada (aprovado)"; agora a pendência explica o motivo e o que fazer.

## Convergência (`/speckit-converge`)

Converged: FR-001 a FR-015 e SC-001 a SC-003 implementados e cobertos por testes
(`req("009:…")`); SC-004 é a aprovação manual da Qualidade; tarefas T001 a T011 concluídas;
nenhuma tarefa nova.

## Pendências a ratificar

- Ordem oficial das partes (a da história 1; variante do projeto DBS com a Alteração logo após a
  capa da Entrada) — Garantia da Qualidade.
- Plano de Negócios no documento com os campos financeiros só para quem tem a permissão, com a
  opção de omiti-los para distribuir à equipe — Gestor de P&D.
- Formato do resumo da trilha (período, eventos por tipo e eventos-chave) — Garantia da Qualidade.
- Aprovação do documento completo de um projeto piloto pela Qualidade (SC-004) e medição da meta de
  300 páginas no servidor de homologação.
