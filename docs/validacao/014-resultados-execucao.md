# Feature 014 — resultados de execução (evidência)

Ambiente de desenvolvimento, 2026-11-12, dados fictícios. Senhas do LDAP de desenvolvimento.
Destino de cópias `var/backups` (montado em `/app/var/backups`, sistema de arquivos diferente do
volume de dados). Imagem com `pg_dump`/`pg_restore` 17.11 (repositório PGDG).

## Suíte automatizada

| Item | Resultado |
| --- | --- |
| Testes (`pytest`) | 1.255 aprovados (todas as features até a 014), 0 falhas; cobertura `sgp/core` 93,5% e `sgp/audit` 97,1% |
| Testes da feature (`tests/operations`) | 27 aprovados; cópia e restauração com `pg_dump`/`pg_restore` reais no PostgreSQL 17, em transação real |
| Matriz de rastreabilidade | 309 requisitos, 0 sem cobertura (a primeira rodada do portão apontou 014:FR-010 e FR-015 sem teste; ganharam testes de rotas e dos roteiros) |
| SC-001 restauração | C1 a C6 aprovadas; gravação feita durante o `pg_dump` não foi bloqueada e ficou fora do manifesto e do banco restaurado; contagens do banco em uso iguais antes e depois |
| SC-002 danos | manifesto alterado (C1), banco copiado alterado (C2), arquivo do acervo alterado ou ausente (C6) e trilha adulterada (C5, com o aviso de incidente já apontado pela verificação da trilha) reprovam e avisam por e-mail |
| SC-003 configuração inválida | depuração ligada, chave de desenvolvimento, migração pendente, destino de cópias dentro dos dados, diretório e e-mail não configurados reprovam o item com o motivo; valores de segredo nunca aparecem |
| Cópia | manifesto com resumos, contagens e último evento da trilha; acervo endereçado pelo SHA-256 com cópia conferida; segunda cópia sem arquivos novos; uma cópia por vez; arquivo ausente ou alterado reprova a cópia mas mantém o banco copiado e o manifesto com os problemas; retenção de 35 dias com a mensal mantida |
| Qualificações | IQ-01 a IQ-24 e OQ-01 a OQ-11; relatório PDF/A guardado com SHA-256; execução imutável (ORM e gatilho); IQ só para a TI; OQ para a TI e a Qualidade |

## Roteiro do quickstart na pilha real

Rodada 1 (antes do ajuste de comportamento descrito abaixo):

| Cenário | Resultado |
| --- | --- |
| Painel "Operação e validação": `admin.ti` com "Fazer cópia agora" e avisos de cópia atrasada e de teste não executado; `qualidade.ar` sem o botão de cópia e com a OQ; `ana.analista`: 403; item de menu só para TI e Qualidade | aprovado |
| `qualidade.ar` pede cópia: 403; `admin.ti` pede: "Cópia de segurança pedida" | aprovado |
| A cópia pelo worker **falhou**: `cert.pdf` (arquivo 2) tem conteúdo diferente do resumo guardado — é o arquivo adulterado de propósito no roteiro da feature 003 ("arquivo alterado direto no volume de armazenamento"); o aviso por e-mail chegou à TI | detecção correta; revelou que um arquivo com problema impedia a cópia do banco (ajustado: ver rodada 2) |
| IQ pelo comando: 19 itens aprovados; reprovados IQ-06 e IQ-07 (depuração ligada), IQ-11 (EMAIL_HOST, DEFAULT_FROM_EMAIL e SITE_URL não definidos no ambiente), IQ-23 (e-mail em arquivo) e IQ-24 (estáticos não coletados) — esperado: o ambiente de desenvolvimento não é qualificado; IQ-16 aprovado (destino em outro sistema de arquivos) | aprovado (comportamento esperado) |
| OQ pela tela (Qualidade): OQ-02 a OQ-05 recusados pelo banco ("permission denied" para o papel da aplicação), OQ-06 PDF/A de teste selado e selo válido, OQ-07 worker e agendamentos, OQ-11 nenhuma contagem alterada; OQ-01 reprovado (ver abaixo), OQ-08 e OQ-09 reprovados (sem cópia) | aprovado (comportamento esperado) |
| Relatório da OQ baixado pela Qualidade (PDF com OQ-01 a OQ-11 e o executor); `ana.analista`: 403; `UPDATE` direto na execução recusado pelo gatilho | aprovado |
| Revisão de acessos: CSV (`;`) com 7 pessoas e as colunas do contrato, XLSX; `ana.analista`: 403 | aprovado |

Ajuste depois da rodada 1: arquivo ausente ou alterado continua reprovando a cópia (spec, casos
extremos), mas o banco copiado e o manifesto com a lista de problemas ficam na pasta da cópia, para
que um único arquivo com problema não deixe o banco sem cópia; a retenção também remove essas
pastas depois de 35 dias. Teste `test_arquivo_alterado_nao_entra_no_acervo`.

Rodada 2:

| Cenário | Resultado |
| --- | --- |
| Cópia pelo comando com o `cert.pdf` adulterado: reprova com "1 com conteúdo diferente do resumo guardado no sistema: c314275fd170", mantém `banco.dump` e `manifesto.json` com `problemas: [[c314…, "alterado"]]` | aprovado |
| Reparo verificável do `cert.pdf` (dado fictício; o roteiro da 003 acrescentou 10 bytes): truncado para os 47 bytes registrados, o SHA-256 voltou a ser exatamente o registrado (`c314275f…152c`) | aprovado |
| Cópia pela tela: bem-sucedida, 22 arquivos (1 novo), trilha até o evento 871, cópia mensal, resumo do manifesto conferido no destino; segunda cópia pelo comando: 0 arquivos novos | aprovado |
| Teste de restauração pela tela: C1, C2, C3 (restaurado em `sgp_restauracao`), C4 (75 tabelas, 2.324 linhas) e C6 (22 arquivos) aprovadas; **C5 reprovada**: "1 quebra na cadeia restaurada: evento 3 (conteúdo alterado). A verificação da trilha do banco em uso já aponta a mesma quebra: incidente existente, reproduzido fielmente pela cópia"; banco isolado descartado; e-mail de aviso à TI | aprovado (comportamento esperado) |
| OQ pela tela: OQ-08 aprovado (cópia em dia); OQ-01 e OQ-09 reprovados pela mesma quebra do evento 3; demais itens como na rodada 1 | aprovado (comportamento esperado) |
| Trilha: `operations.backup_completed`, `backup_failed`, `backup_requested`, `restore_requested`, `restore_tested`, `qualification_requested`, `qualification_executed`, `report_downloaded`, `access_review_exported` | aprovado |

A quebra da trilha no evento 3 é a adulteração feita de propósito no roteiro da feature 001
("alteração direta do evento 3 no banco"; a verificação diária aponta "íntegra: não" desde
08/11/2026). Ela não foi desfeita: a trilha nunca é alterada por fora do sistema. Por isso, no
ambiente de desenvolvimento, OQ-01, C5 e OQ-09 reprovam — corretamente. Em homologação, com banco
novo, a IQ e a OQ são executadas pelos roteiros (SC-004).

## Convergência (`/speckit-converge`)

Avaliação durante a implementação: a linha de comando das qualificações aceitava pessoa da
Qualidade, o que contrariava o esclarecimento (a Qualidade executa a OQ pela tela; a linha de
comando é da TI) e permitiria registrar como executor quem não executou; corrigido (comando só
para o perfil Administrador, teste `test_linha_de_comando_so_para_a_ti`) e contrato atualizado,
junto com a lista `problemas` do manifesto.

Primeira avaliação formal (`/speckit-converge`): uma divergência de documentação (baixa) — o
plano e a pesquisa descreviam a C5 por apelido de banco criado em tempo de execução, e o código
percorre a cadeia restaurada com `walk_rows` numa conexão direta; virou a tarefa T018 (plano e
pesquisa atualizados).

Segunda avaliação: Converged — FR-001 a FR-015 e SC-001 a SC-003 implementados e cobertos por
testes (`req("014:…")`); SC-004 é a execução em homologação (verificação manual); tarefas
T001 a T018 concluídas; nenhuma tarefa nova.

## Pendências a ratificar e dependências

- Destino das cópias em outro servidor ou compartilhamento da rede, cópia fora do prédio e acesso
  restrito à TI — TI (respostas provisórias do esclarecimento, sessão 2026-11-12).
- Retenção: diárias por 35 dias e a primeira bem-sucedida de cada mês sem remoção automática — TI
  e Garantia da Qualidade.
- Cópias sem cifragem pelo sistema, protegidas pelo destino e pela cifragem do armazenamento da
  infraestrutura — TI e Garantia da Qualidade.
- Quem executa a IQ (TI) e a OQ (TI e Qualidade) e por onde — TI e Garantia da Qualidade.
- Tratamento de arquivo guardado ausente ou alterado e de quebra da trilha como incidente da
  qualidade (registro, investigação e decisão) — Garantia da Qualidade; o sistema aponta, avisa e
  mantém o banco copiado, mas não tem fluxo de aceite do incidente.
- Execução da IQ e da OQ em homologação e assinatura dos roteiros (SC-004) — TI e Garantia da
  Qualidade; plano e relatório de validação e qualificação de desempenho (piloto) — Garantia da
  Qualidade e Gestor de P&D.
- Checklists `recuperacao-integridade.md` e `evidencias-validacao.md` aguardam a revisão (marcação)
  pela TI e pela Garantia da Qualidade.
