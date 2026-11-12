# Feature 007 — resultados de execução (evidência)

Ambiente de desenvolvimento, 2026-11-11, dados fictícios. Senhas do LDAP de desenvolvimento.

## Suíte automatizada

| Item | Resultado |
| --- | --- |
| Testes (`pytest`) | 968 aprovados (todas as features até a 007 e a 013), 0 falhas |
| Cobertura `sgp/core` / `sgp/audit` | 93,5% / 97,1% |
| Matriz de rastreabilidade | 211 requisitos, 0 sem cobertura |
| SC-001 vetores de referência | V1 a V8 de docs/contexto/06-casos-de-teste.md reproduzidos (média, DP amostral e populacional, CV, NumAcc1, regressões, Clopper-Pearson, Wilson, arredondamentos) |
| Propriedades (hypothesis) | média entre mínimo e máximo, DP invariante a deslocamento, arredondamento idempotente, IC contém a proporção |
| SC-003 bloqueio | aprovação do RAPD bloqueia os estudos vinculados; editar recusado; nova versão preserva a anterior no conteúdo aprovado |
| SC-004 desempenho | 500 medidas calculadas em menos de 2 s |
| SC-005 importação | pré-visualização de 1.000 linhas em menos de 10 s |

## Roteiro do quickstart na pilha real

| Cenário | Resultado |
| --- | --- |
| `ana.analista` cria no PD-2026-001 um estudo de repetibilidade vinculado ao RAPD (tópico 2) com critério "CV% < 15" | aprovado |
| Medidas 2, 4, 4, 4, 5, 5, 7, 9: média 5,00; DP 2,14; CV 42,76% (meio para o par, 2 casas); "não atendido" | aprovado |
| Mudar o critério depois das medidas: recusado | aprovado |
| Importação CSV com `;` (equipamento "Leitor-dev"): 3 linhas aceitas e 1 recusada com o motivo; confirmação grava; inclinação 2,0000, intercepto 1,0000, R² 1,0000; mapeamento salvo | aprovado |
| Não aplicável sem justificativa recusado; com justificativa aceito | aprovado |
| `leitor.consulta` sem acesso ao projeto: 403 | aprovado |
| PDF do RAPD (006): tabelas "Medidas – …" e "Resultados – …" numeradas e conclusão "CV% < 15: não atendido (42,76)" | aprovado |
| Trilha: `studies.created`, `criteria_set`, `updated`, `imported`, `mapping_saved`, `not_applicable` | aprovado |

Artefato do roteiro: textos acentuados enviados pelo `curl` do Windows chegam em cp1252 (já
registrado nas features anteriores); por isso a justificativa gravada no roteiro aparece com
caracteres trocados. Pela tela e nos testes automatizados o texto é preservado.

## Pendências a ratificar

- Arredondamento "meio para o par" (conferir o texto vigente da ABNT NBR 5891), casas por tipo de
  resultado e Clopper-Pearson como padrão (Wilson como opção).
- Formatos próprios de equipamento: dependem de arquivos de exemplo de P&D.
- Estudos obrigatórios por tecnologia: a definir pela Qualidade (hoje a obrigatoriedade vem da
  Entrada).
- Lista de vetores de referência (V1 a V8) a aprovar pela Garantia da Qualidade.
- Estabilidade com pelo menos três lotes (art. 58, VII): a regra de completude fica para o dossiê
  (feature 011).
