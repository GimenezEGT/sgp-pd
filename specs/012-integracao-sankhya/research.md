# Research: Integração com o Sankhya

## R1. Cliente HTTP isolado, só pelo API Gateway

- **Decision**: `sgp/integrations/sankhya.py` com a biblioteca padrão (`urllib.request`), sem
  dependência nova: autenticação OAuth 2.0 client credentials em `{SANKHYA_BASE_URL}/authenticate`
  (form data `client_id`, `client_secret`, `grant_type=client_credentials` e header `X-Token`);
  token guardado no cache até 60 s antes de expirar e renovado automaticamente (também depois de
  uma resposta 401); chamadas em
  `{SANKHYA_BASE_URL}/gateway/v1/mge/service.sbr?serviceName=<serviço>&outputType=json` com
  `Authorization: Bearer`. Nenhum acesso ao banco do ERP.
- **Rationale**: o contexto (07) fixa o gateway como única via; a biblioteca padrão basta para POST
  com JSON e form data e é fácil de simular nos testes.

## R2. Corpo das chamadas (provisório)

- **Decision**: `CRUDServiceProvider.loadRecords` e `CRUDServiceProvider.saveRecord` no formato
  público da documentação (`{"serviceName", "requestBody": {"dataSet": {"rootEntity", "dataRow":
  {"localFields": {...}}, ...}}}`), montado num único módulo (`payloads.py`), marcado como
  provisório até a consultoria confirmar a referência "Incluir e Alterar Dados" e "Como consultar
  dados?" (o contexto pede essa confirmação).

## R3. Mapeamento configurável das tabelas adicionais

- **Decision**: entidades e campos de cada registro do modelo lógico do contexto (Projeto P&D,
  Documento P&D, Lote P&D, Insumo novo, Resultado de estudo, Produto para consulta) num YAML
  versionado mantido pela TI pela tela, como a definição do dossiê; a versão padrão não inventa
  nomes: vem com as entidades vazias e, sem mapeamento, as mensagens ficam "aguardando
  configuração" (a exportação em arquivo funciona do mesmo jeito).

## R4. Outbox na mesma transação e idempotência

- **Decision**: `IntegrationMessage` criada na transação da aprovação (sinal da trilha:
  `signatures.approved` de subdocumento, `projects.approved` e aprovação da Saída com insumos
  novos), com chave de idempotência `<registro>:<id>:<versão>` única; o envio (tarefa Celery logo
  depois do commit e varredura periódica pelo beat) faz `saveRecord` com a chave como chave
  primária do registro adicional, o que torna o reenvio uma atualização do mesmo registro;
  tentativas com espera exponencial (1, 2, 4, 8… minutos, até 6 tentativas automáticas), último erro
  e próxima tentativa guardados; a TI reprocessa manualmente.

## R5. Consulta de produto

- **Decision**: busca por código pela entidade de produtos mapeada, com descrição, unidade e
  situação; na tela de insumos e lotes, um botão consulta e mostra o resultado (HTMX); com o ERP
  indisponível ou a integração desligada, o cadastro continua e o aviso diz que o código não foi
  conferido.

## R6. Contingência em arquivo

- **Decision**: exportação das mensagens por registro em CSV (UTF-8, ";", vírgula decimal), XLSX e
  JSON com o envelope do contexto (`{"entidade", "gerado_em", "registros"}`), um arquivo por
  registro, com evento na trilha.

## R7. Testes com servidor simulado

- **Decision**: um servidor HTTP local em thread nos testes simula `/authenticate` e o gateway
  (`loadRecords` e `saveRecord` com gravação por chave primária), conta chamadas e pode falhar sob
  comando; os testes cobrem token, renovação, idempotência, falha e reprocessamento.
