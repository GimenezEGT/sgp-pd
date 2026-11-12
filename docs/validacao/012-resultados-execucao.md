# Feature 012 — resultados de execução (evidência)

Ambiente de desenvolvimento, 2026-11-12, dados fictícios. Senhas do LDAP de desenvolvimento.
Integração desligada (`SANKHYA_ENABLED=false`, sem credenciais): não há ambiente de testes da
Sankhya disponível; o gateway foi exercitado nos testes automatizados com um servidor HTTP simulado.

## Suíte automatizada

| Item | Resultado |
| --- | --- |
| Testes (`pytest`) | 1.204 aprovados (todas as features até a 013), 0 falhas; cobertura `sgp/core` 93,5% e `sgp/audit` 97,1% |
| Testes da feature (`tests/integrations`) | 15 aprovados, com servidor simulado do gateway (`/authenticate` e `service.sbr`) |
| Matriz de rastreabilidade | 290 requisitos, 0 sem cobertura (a primeira rodada do portão apontou o 012:FR-009 sem marcação; os testes de envio, falha e exportação, que já conferiam os eventos, receberam o marcador) |
| FR-001 gateway oficial | token OAuth 2.0 (client credentials) com `X-Token`, guardado em cache; renovação única depois de 401; erro 5xx e tempo esgotado tratados como indisponibilidade; recusa do serviço (`status` diferente de 1) vira erro com a mensagem do gateway |
| FR-002 credenciais | só nas variáveis `SANKHYA_*`; nenhuma mensagem de erro inclui credencial ou token; `.env.example` sem valores |
| SC-001 envio único | aprovação gera uma mensagem por chave de idempotência; reenvio da mesma mensagem atualiza o mesmo registro no gateway simulado; nova chamada de `enqueue` com a mesma chave não cria mensagem |
| SC-004 falha do gateway | a aprovação conclui com o gateway falhando; a mensagem fica com erro, tentativas e próxima tentativa em espera crescente (1, 2, 4… minutos) até o limite; o reprocessamento pela TI envia; o gestor não reprocessa |
| FR-006 insumo novo | Saída aprovada com matérias-primas e materiais de embalagem novos gera registros "Insumo novo" com situação "solicitado", fabricante e certificado |
| SC-003 exportação | CSV (";", UTF-8), XLSX e JSON (envelope `entidade`, `gerado_em`, `registros`) reproduzem a fila; só a TI exporta |

## Roteiro do quickstart na pilha real

| Cenário | Resultado |
| --- | --- |
| Migrações `integrations.0001` e `0002` aplicadas; mapeamento versão 1 semeado ("entidades a definir com a consultoria Sankhya") | aprovado |
| Worker com as tarefas `sgp.integrations.dispatch` e `process_due`; beat com "fila-de-integracao-sankhya" a cada 5 minutos | aprovado |
| Entrada do PD-2026-001: nova versão 03, envio por `ana.analista` e aprovação por `gestor.pd` com a senha de rede; a aprovação gera a mensagem `documento:1:3`, que o worker deixa "aguardando configuração" (0 tentativas); o subdocumento fica aprovado | aprovado |
| Conteúdo da mensagem: código do projeto, tipo e versão do subdocumento, versão do formulário, elaborador, aprovador e resumo SHA-256 (64 caracteres) do conteúdo aprovado | aprovado |
| `admin.ti` vê a fila com o aviso de integração desligada, a chave e a situação; filtros por situação e registro; reprocessar uma mensagem sem configuração: "Mensagem reprocessada: Aguardando configuração."; `gestor.pd` reprocessando: 403 | aprovado |
| Exportação de contingência dos documentos: CSV (`text/csv; charset=utf-8`, cabeçalho com `chave` e os 11 campos do contrato separados por ";"), XLSX (aba "Documento P&D") e JSON (envelope do contexto), com o mesmo registro nos três; formato inválido recusado com mensagem; `ana.analista` exportando: 403 | aprovado |
| Consulta de produto no formulário de insumos e de lotes ("Consultar no Sankhya"; o de kits não tem o botão): "Código não conferido no Sankhya: Integração com o Sankhya desligada ou sem mapeamento de produtos. O cadastro continua normalmente."; sem código: "Informe o código do produto." | aprovado |
| Mapeamento: YAML com campo lógico inexistente e entidade sem chave recusado com as duas mensagens; o mapeamento padrão republicado vira a versão 2; `UPDATE` direto na versão 1 recusado pelo gatilho de imutabilidade; `gestor.pd` na tela do mapeamento: 403 | aprovado |
| Fila para `ana.analista`, `gestor.pd`, `qualidade.ar` e `leitor.consulta`: 403; item "Integração com o Sankhya" só no menu da TI | aprovado |
| Trilha: `integration.exported` 3, `integration.reprocessed` 1, `integration.mapping_published` 1 (envio e falha só com o gateway, cobertos pelos testes) | aprovado |

## Convergência (`/speckit-converge`)

Ver a seção ao fim deste arquivo, preenchida depois da avaliação.

## Pendências a ratificar e dependências

- Entidades, campos e chaves do Sankhya para cada registro (tabelas adicionais `AD_*`) e a entidade
  de produtos para a consulta — consultoria Sankhya e TI; até lá as mensagens ficam "aguardando
  configuração" e a exportação em arquivo é a contingência.
- Corpo das chamadas `CRUDServiceProvider.saveRecord` e `loadRecords` (research R2, provisório) a
  confirmar com a consultoria no ambiente de testes da Sankhya.
- Credenciais do ambiente de testes e de produção (client_id, client_secret, X-Token) e usuário de
  integração com permissões mínimas no Sankhya — TI e consultoria.
- SC-002: conferir a consulta de um insumo real pelo código em homologação, depois do mapeamento e
  das credenciais (registrado em `docs/validacao/verificacoes-manuais.json`).
- Envio imediato com novas tentativas em espera crescente (até `INTEGRATION_MAX_ATTEMPTS`, 6 por
  padrão) e reprocessamento manual — TI.
- Insumo novo como solicitação de cadastro, sem cadastro direto do produto no ERP — Gestor de P&D,
  Produção e TI.
