# Feature 011 — resultados de execução (evidência)

Ambiente de desenvolvimento, 2026-11-12, dados fictícios. Senhas do LDAP de desenvolvimento.

## Suíte automatizada

| Item | Resultado |
| --- | --- |
| Testes (`pytest`) | 1.174 aprovados (todas as features até a 011 e a 013), 0 falhas; cobertura `sgp/core` 93,5% e `sgp/audit` 97,1% |
| Testes da feature (`tests/dossier`) | 22 aprovados |
| Matriz de rastreabilidade | 277 requisitos, 0 sem cobertura |
| SC-001 final bloqueado | com item obrigatório faltando só sai rascunho (marca d'água, lista de pendências, sem pacote) |
| SC-002 aditamento | depois do envio, mudar um complemento e gerar de novo: o aditamento traz só esse item, na tela e no PDF |
| SC-003 árvore de títulos | I a XII em ordem no PDF e nos títulos de nível 1 do DOCX, iguais à estrutura do contexto |
| Checagem | classe da Entrada aprovada; fora da classe com a justificativa da definição (VI na classe I, VIII nas classes I e II); não aplicável com justificativa da origem ou do complemento; sem justificativa conta como faltando; família com dois kits |
| Final | declaração do responsável técnico e legal com o texto do contexto, nome do produto em itálico no DOCX, anexos citados e no pacote ZIP, textos padrão aprovados registrados na versão |
| Textos padrão | versões; aprovação só por outra pessoa e com a senha de rede (005); versão anterior substituída |
| Envio | rascunho e classe I não são enviados; protocolo, data e resultado registrados |

## Roteiro do quickstart na pilha real

| Cenário | Resultado |
| --- | --- |
| `qualidade.ar` cadastra a empresa e o responsável técnico e legal (dados fictícios) | aprovado |
| Textos padrão "unidade-fabril" e "processo-fabricacao" gravados pela Qualidade; a autora tentando aprovar: "Quem escreveu o texto não pode aprová-lo."; `gestor.pd` aprova com a senha de rede: versão 1 aprovada | aprovado |
| Entrada do PD-2026-001 (aprovada antes da 005) ganha a versão 02 pela assinatura: nova versão, envio e aprovação; versão congelada com classe II | aprovado |
| Checagem do dossiê: classe II; 11 itens completos, 31 faltando e 3 não aplicáveis (VIII fora da classe), com origem e motivo | aprovado |
| Complemento do item I.A.1 (Analito) e item V marcado como não aplicável com justificativa | aprovado |
| Geração: rascunho versão 01 (itens faltando); PDF com I a XII em ordem depois da lista de pendências, cabeçalho "Dossiê Técnico <produto>", rodapé com a razão social, marca d'água e texto padrão aprovado no item X; DOCX com 12 títulos de nível 1 e cabeçalho em itálico | aprovado |
| Item V: "Não aplicável. <justificativa>" no PDF (versão 02, depois de regravar a justificativa por arquivo) | aprovado |
| `ana.analista` vê o dossiê (200) e não gera (403); `leitor.consulta` sem acesso: 403; definição visível para qualquer perfil; aditamento sem envio anterior avisa que não há versão enviada | aprovado |
| Trilha: `dossier.company_updated`, `text_saved` 2, `text_approved` 2, `supplement_saved`, `generated`, `downloaded` | aprovado |

Artefato do roteiro: a primeira justificativa do item V foi enviada pelo `curl` do Windows como
argumento e chegou com os acentos trocados (conversão cp1252, já registrada nas features
anteriores); regravada por arquivo, saiu correta. O dossiê final, o pacote com anexos, o envio, o
resultado e o aditamento foram exercitados nos testes automatizados com um projeto completo.

## Convergência (`/speckit-converge`)

Converged: FR-001 a FR-013 e SC-001 a SC-003 implementados e cobertos por testes
(`req("011:…")`); SC-004 é a conferência manual de Assuntos Regulatórios; tarefas T001 a T011
concluídas; nenhuma tarefa nova.

## Pendências a ratificar e dependências

- Estrutura I a XII a conferir contra o Manual para Regularização de Dispositivos para Diagnóstico
  in Vitro (ANVISA, 25/08/2026), incluindo as letras atribuídas pelo sistema (I.F e VI.B a VI.M) —
  Assuntos Regulatórios.
- Anexos em arquivos separados no pacote, com a lista no dossiê — Assuntos Regulatórios.
- Assinatura do responsável técnico e legal fora do sistema (ICP-Brasil ou plataforma de
  peticionamento), com o PDF assinado anexado no envio — Assuntos Regulatórios e Jurídico.
- Aplicabilidade por classe da definição padrão (estabilidade em todas as classes; desempenho
  analítico nas classes II a IV; clínico nas III e IV) — Assuntos Regulatórios.
- Regra de família (mesmo nome de família, tecnologia e classe) — Assuntos Regulatórios.
- Os `.docx` originais dos dossiês não estão em `docs/modelos`: a comparação com os originais fica
  para quando forem disponibilizados.
