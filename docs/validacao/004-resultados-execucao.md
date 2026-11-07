# Feature 004 — resultados de execução (evidência)

Ambiente de desenvolvimento, 2026-11-07, dados fictícios.

## Suíte automatizada

| Item | Resultado |
| --- | --- |
| Testes (`pytest`) | 689 aprovados (todas as features até a 004, com a convergência), 0 falhas |
| Cobertura `sgp/core` / `sgp/audit` | 93,5% / 97,1% |
| Matriz de rastreabilidade | 110 requisitos (001 a 004), 0 sem cobertura |
| SC-001 modelos versão 05 | nove tipos publicados e válidos no JSON Schema |
| SC-005 gravação com 100 linhas de tabela | abaixo de 2 s |

## Roteiro do quickstart na pilha real (Nginx HTTPS → Django → OpenLDAP → PostgreSQL)

| Cenário | Resultado |
| --- | --- |
| Lista de modelos com as nove versões 05; capa da Entrada com "9 - Classificação de Risco (RDC 830/2023)" e "13 - Outros dados pertinentes" | aprovado |
| `ana.analista` tenta criar nova versão de modelo: 403 | aprovado |
| `qualidade.ar` cria o rascunho da versão 06 do RAPD e publica; o RAPD criado depois nasce no "Formulário Versão: 06" | aprovado |
| Entrada no projeto `PD-2026-001`: "não se aplica" sem justificativa recusado; Entrada completa gravada | aprovado |
| Aprovação: `ana.analista` recebe 403; `gestor.pd` aprova (situação Aprovado) | aprovado |
| Lote Piloto antes da Formulação aprovada: aviso; `gestor.pd` autoriza com motivo; criação segue | aprovado |
| Validação com pendências dos requisitos "aplica" e os "não se aplica" com justificativa | aprovado |
| Verificação Final com "Previsto" da Entrada ("Tipos de amostra: Soro; Plasma") e linha "Não aplicável" dos filtros; disposição "Reprovado" sem justificativa recusada | aprovado |
| Saída em projeto ANVISA sem os itens MAPA e renumerada (tópico 10 = setores de transferência) | aprovado |
| Alteração com "Versão alterada: 01 · Nova Versão: 02"; aprovação recusada sem análise de risco; aprovada com análise: projeto na versão 02, Formulação e Entrada marcadas para revisão, evento na trilha | aprovado |

Observação do roteiro: o `curl` do Windows envia argumentos com acento na página de código do
sistema (cp1252), por isso textos com acento digitados no roteiro chegaram com caractere de
substituição; os navegadores enviam UTF-8. A conferência desses dois textos foi feita no banco.

## Pendências que dependem de terceiros

- Ratificar com o Gestor de P&D: ordem recomendada com autorização, editores dos subdocumentos e
  controle otimista na edição simultânea.
- Ratificar com a Garantia da Qualidade e Assuntos Regulatórios: rótulo do tópico 9 da Entrada,
  Análise Crítica com 3 tópicos e a regra de pré-preenchimento do "Realizado" (pendente).
- A aprovação desta feature é provisória; a feature 005 a substitui pela assinatura eletrônica.
