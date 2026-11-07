# 06 — Casos de teste: regras de validação e vetores de referência

Os arquivos de `docs/modelos/` servem só como referência de estrutura e layout; os dados neles são fictícios e não são usados aqui. Os vetores abaixo são sintéticos ou vêm de conjuntos de referência certificados; a Qualidade deve aprovar a lista final.

## A. Regras de validação (cada uma vira ao menos um teste)

| # | Regra | Teste |
| --- | --- | --- |
| 1 | Linhas de tabelas de resultados são numeradas pelo sistema | Tabela com 118 linhas sai numerada de 1 a 118, sem lacunas |
| 2 | O cabeçalho de uma tabela de lote vem do lote referenciado | Tabela do lote B mostra o código e as datas do lote B |
| 3 | "Não aplicável" e lista preenchida são mutuamente exclusivos | Salvar "não aplicável" com itens é rejeitado com mensagem clara |
| 4 | Códigos de insumo só por referência ao cadastro | A tela não oferece campo livre de código |
| 5 | Totais são sempre calculados | Total não é editável e é igual à soma das parcelas |
| 6 | Referências cruzadas ("ver item VIII") são resolvidas na geração | Mover um item atualiza todas as referências a ele |
| 7 | Um valor (ex.: concentração de um interferente) é cadastrado uma vez e reutilizado | Texto e tabela leem o mesmo valor; alterar o cadastro altera os dois |
| 8 | Estatísticas são sempre calculadas a partir dos dados guardados | Não existe campo para digitar média, DP ou CV% |
| 9 | Tipo de estudo vem de vocabulário controlado | O tipo é seleção, não texto livre |
| 10 | Lotes citados na Saída e no dossiê vêm das referências da Validação | Saída, Validação e dossiê do mesmo projeto citam os mesmos lotes |
| 11 | Contagens de testes e amostras são calculadas a partir dos estudos | Total do documento = soma dos estudos registrados |
| 12 | Modelo publicado tem rótulos únicos e numeração automática | Publicar modelo com dois tópicos de mesmo rótulo gera aviso; a numeração nunca repete |
| 13 | CV% com média zero não é calculado | Resultado aparece como "não calculável", sem erro |

## B. Vetores de referência

Desvio-padrão amostral (n − 1), salvo indicação.

| # | Caso | Dados | Resultado esperado |
| --- | --- | --- | --- |
| V1 | Média, DP e CV% | 2; 4; 4; 4; 5; 5; 7; 9 | média 5; DP amostral 2,13809; DP populacional 2; CV 42,76% |
| V2 | Precisão numérica (NIST StRD, conjunto NumAcc1) | 10000001; 10000003; 10000002 | média 10000002; DP 1 |
| V3 | Regressão exata | x: 1; 2; 3; 4 · y: 3; 5; 7; 9 | y = 2x + 1; R² = 1 |
| V4 | Regressão com ruído | x: 1; 2; 3; 4; 5 · y: 1,1; 1,9; 3,2; 3,8; 5,1 | inclinação 0,99; intercepto 0,05; R² 0,9892 |
| V5 | IC 95% exato de Clopper-Pearson | 45/50; 18/20; 20/20; 0/20 | 78,19% a 96,67%; 68,30% a 98,77%; 83,16% a 100%; 0% a 16,84% |
| V6 | IC 95% de Wilson (se for o método escolhido) | 45/50 | 78,64% a 95,65% |
| V7 | Regra de arredondamento em 3 casas | 1,0349; 0,1245; 0,1235 | truncar: 1,034; 0,124; 0,123 · meio para cima: 1,035; 0,125; 0,124 · meio para o par: 1,035; 0,124; 0,124 |
| V8 | Arredondamento para inteiro | 2,5 | truncar 2 · meio para cima 3 · meio para o par 2 |

Para regressão e estatística descritiva, os conjuntos certificados do NIST Statistical Reference Datasets (StRD) servem de evidência adicional na validação do sistema.
