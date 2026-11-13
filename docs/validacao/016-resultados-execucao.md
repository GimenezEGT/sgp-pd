# Feature 016 — resultados de execução (evidência)

Ambiente de desenvolvimento, 2026-11-13, dados fictícios. Origem: pedido do usuário — "cada
subdocumento deve ter sua própria versão, e o documento final deve ter também sua própria versão que
muda sempre que um subdocumento muda de versão. Tudo isso com rastreabilidade." Respostas do próprio
usuário no esclarecimento (não provisórias): a versão do documento final sobe na aprovação da nova
versão da parte; o histórico dos projetos existentes é reconstruído a partir das aprovações.

## Suíte automatizada

| Item | Resultado |
| --- | --- |
| Testes (`pytest`) | 1.274 aprovados (todas as features até a 016), 0 falhas; teste lento de 300 páginas também aprovado |
| Testes da feature (`tests/fulldoc/test_final_versions.py`) | 11 aprovados |
| Matriz de rastreabilidade | 332 requisitos, 0 sem cobertura |
| SC-001 uma versão por aprovação | aprovação do projeto gera a 01 (TAP e Plano numa só versão); aprovação da Entrada gera a 02 ("Entrada de Projeto: — → 01"); nova versão em rascunho, envio e devolução não mudam a versão; a aprovação seguinte gera a 03 ("01 → 02"); Alteração de Projeto também gera versão; composição com versão, data e resumo de cada parte; registro imutável (gatilho recusa UPDATE) |
| SC-002 documento gerado | recomposição registrada antes de gerar quando a composição vigente não está registrada; documento aponta para a versão; nome "… v02.pdf"; capa com "VERSÃO DO DOCUMENTO FINAL" e "VERSÃO DO PROJETO"; parte "Versões do documento final"; o pedido repetido reaproveita o mesmo documento; verificação pública do código mostra "02 do documento final (projeto NN)" |
| SC-003 rastreabilidade na tela | seção "Versões do documento final" com o que mudou, motivo e composição; coluna "Versão do documento final" nos documentos gerados; "Histórico de versões" no subdocumento, no TAP e no Plano de Negócios |
| FR-009 reconstrução | aprovações em ordem de data, TAP e Plano do mesmo aprovador numa só versão, versões "Reconstruída", idempotente; evento na trilha de cada versão reconstruída pelo "sistema", com data e aprovador originais no valor, sem repetir |

## Conferência na pilha real

### Reconstrução (migração ao subir o `web`)

| Projeto | Aprovações registradas | Versões reconstruídas |
| --- | --- | --- |
| PD-2026-001 (roteiro) | Formulação v01 e v02; Entrada v02 e v03 (a v01 da Entrada foi aprovada antes da feature 005, sem registro de versão aprovada) | 01 "Elaboração de Formulação: — → 01"; 02 "01 → 02"; 03 "Entrada de Projeto: — → 02"; 04 "Entrada de Projeto: 02 → 03" |
| PD-2026-002 (roteiro) | TAP v01 e Plano v01 no mesmo instante | 01 "Termo de Abertura do Projeto: — → 01; Plano de Negócios: — → 01" |
| PD-2026-003 (teste do usuário) | TAP v01 e Plano v01; Entrada v01 | 01 (TAP e Plano); 02 "Entrada de Projeto: — → 01" |

Achado e correção: logo depois da migração, as 7 versões reconstruídas não tinham evento na trilha
(a trilha não aceita data passada e a migração não gravava evento). Corrigido no mesmo ciclo: depois
das migrações, o app grava `fulldoc.version_created` para cada versão reconstruída sem evento, pelo
"sistema", com o motivo "Reconstrução a partir das aprovações registradas (feature 016)" e a data e o
aprovador originais no valor. Ao religar o `web`, os 7 eventos foram gravados (teste automatizado
`test_versoes_reconstruidas_entram_na_trilha`).

### Roteiro de escrita (PD-2026-001, projeto de roteiro)

| Passo | Resultado |
| --- | --- |
| `ana.analista` abre a versão 03 da Elaboração de Formulação, com motivo | "Versão 03 criada em rascunho."; documento final continua na 04 |
| `ana.analista` envia e assina como Elaborado | "Documento enviado para revisão e assinado como Elaborado."; documento final continua na 04 |
| `gestor.pd` aprova e assina | "Documento aprovado e assinado; a versão foi congelada."; nova versão 05, motivo Aprovação, por `gestor.pd`, "Elaboração de Formulação: 02 → 03", 2 partes; evento `fulldoc.version_created` com a mudança |
| Tela "Documento completo" (`lider.projeto`) | seção "Versões do documento final" com as versões 01 a 05, o que mudou, motivo e composição (parte, versão, data de aprovação, resumo) |
| Geração do documento completo (resumido) | pedido concluído pelo worker: "Documento completo PD-2026-001 v05.pdf", versão do documento final 05, versão do projeto 02, rascunho (9 pendências), 16 páginas; capa "VERSÃO DO DOCUMENTO FINAL 05 · VERSÃO DO PROJETO 02"; parte "Versões do documento final" depois do "Quadro de versões", com as 5 versões; na tabela de documentos gerados, 05 no novo e "—" nos gerados antes da 016 |
| "Histórico de versões" da Formulação | 01 Substituída (Criação; documento final 01); 02 Substituída (documento final 02, 03, 04); 03 Vigente (motivo do roteiro; documento final 05) |

Observação do roteiro: o motivo da versão 03 foi enviado pelo `curl` do terminal do Windows fora de
UTF-8, então os acentos ficaram gravados como caractere de substituição ("fict�cio"). É limitação do
roteiro (o navegador envia UTF-8), não do sistema; o registro fica como foi gravado (registro assinado
não se altera).

### Consulta no PD-2026-003 (teste do usuário, somente leitura)

| Tela | Resultado |
| --- | --- |
| "Documento completo" (`gestor.pd`) | versões 01 e 02 "Reconstruída", com a composição de cada uma |
| Entrada de Projeto | "Histórico de versões": 01 Vigente, criada por Ana Analista (fictícia), aprovada por Gestor de P&D (fictício), documento final 02 |
| Projeto | "Histórico de versões" do TAP e do Plano de Negócios |

Trilha ao fim do roteiro: `fulldoc.version_created` — 7 pelo "sistema" (reconstrução) e 1 por
`gestor.pd` (aprovação).

## Convergência (`/speckit-converge`)

Primeira avaliação: FR-001 a FR-010, SC-001 a SC-003, os 7 cenários de aceitação e os 4 casos de
borda atendidos; um achado baixo do tipo "não pedido": a linha do tempo do projeto (feature 010)
passou a mostrar a nova versão do documento final sem constar do contrato. Tarefa T013 acrescentada e
feita (linha do tempo registrada no contrato como parte do histórico na tela do projeto, FR-006).
Segunda avaliação: Converged; tarefas T001 a T013 concluídas.

Ainda no ciclo, fora das tarefas originais: a verificação pública do código mostra a versão do
documento final (registrada no contrato) e o teste da ordem das partes do PDF (feature 009) passou a
esperar a parte "Versões do documento final" depois do "Quadro de versões".

## Pendências

- Checklist `rastreabilidade-versoes.md` aguarda a revisão (marcação) da Garantia da Qualidade.
- Nenhuma decisão provisória: as duas respostas do esclarecimento foram dadas pelo usuário.
