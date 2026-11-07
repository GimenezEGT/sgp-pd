# Feature 012 — Integração com o Sankhya

Os dados dos subdocumentos aprovados passam a ser gravados no Sankhya pelo API Gateway oficial, e os códigos de produtos e insumos passam a vir do cadastro do ERP; acesso direto ao banco do ERP não é aceito pela Sankhya.

O que já se sabe da API:

- Autenticação OAuth 2.0 client credentials: `POST https://api.sankhya.com.br/authenticate` com `client_id`, `client_secret`, `grant_type=client_credentials` e o header `X-Token`, obtido na tela "Configurações Gateway" do Sankhya Om.
- Chamadas no padrão `https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=<serviço>&outputType=json`, com o token no header `Authorization`.
- `CRUDServiceProvider.loadRecords` lê registros; `CRUDServiceProvider.saveRecord` insere ou atualiza conforme a chave primária.
- O dicionário de dados marca tabelas e campos criados pela empresa como "adicionais"; é nelas que os registros do P&D devem ficar.

```text
/speckit-specify Integração com o ERP Sankhya para que os dados dos subdocumentos aprovados fiquem armazenados e utilizáveis no ERP, e para que códigos de produtos e insumos venham do cadastro oficial. Leia docs/contexto/07-integracao-sankhya.md.

Histórias:
1. Como analista, ao cadastrar insumos e lotes, busco o código no cadastro de produtos do Sankhya e o sistema traz descrição e unidade, evitando código digitado errado.
2. Quando um subdocumento é aprovado, seus dados estruturados vão para o Sankhya, nas tabelas adicionais definidas com a TI: projeto, subdocumento, versão, data, signatários, campos principais e identificação do PDF oficial.
3. Na Saída de Projeto aprovada, novas matérias-primas e materiais de embalagem viram solicitações de cadastro no Sankhya, com dados e certificados.
4. Como TI, acompanho a fila de integração (enviado, erro, reenviado) e reprocesso falhas sem duplicar registros.
5. Enquanto a API não estiver liberada, exporto os mesmos dados em CSV, XLSX ou JSON no layout combinado.

Regras: integração só pelo API Gateway oficial; credenciais fora do código; cada envio é idempotente e registrado na trilha de auditoria; falha de integração nunca bloqueia o trabalho no sistema.
```

Pontos que o `/speckit-clarify` deve fechar:

- Quais tabelas adicionais e campos a consultoria vai criar no Sankhya.
- Envio imediato na aprovação ou lote noturno.
- Se a nova matéria-prima é cadastrada direto ou entra como solicitação para o cadastro.
- Qual usuário do Sankhya representa o sistema, já que as permissões dele limitam a integração.

```text
/speckit-plan App "integracoes" com cliente HTTP isolado: OAuth 2.0 client credentials em https://api.sankhya.com.br/authenticate (client_id, client_secret e header X-Token) e renovação automática do token. Chamadas ao gateway https://api.sankhya.com.br/gateway/v1/mge/service.sbr com CRUDServiceProvider.loadRecords para consultas e CRUDServiceProvider.saveRecord para gravação. Padrão outbox: MensagemIntegracao gravada na mesma transação da aprovação e enviada por tarefa Celery com retentativas exponenciais e chave de idempotência. Homologação no ambiente de testes da Sankhya antes da produção. Testes com servidor HTTP simulado.
```

Checklists sugeridos: segurança de credenciais e integridade (idempotência).

Pronto quando:

- [ ] A busca de insumo pelo código traz os dados do Sankhya em homologação.
- [ ] Uma aprovação gera um único registro no Sankhya, mesmo com reenvio.
- [ ] A exportação em arquivo funciona como contingência.

---

Depois do `/speckit-plan`: rode `/speckit-checklist` com os temas sugeridos, `/speckit-tasks`, `/speckit-analyze` e `/speckit-implement`; repita `/speckit-implement` e `/speckit-converge` até o relatório dizer Converged. Faça commit ao fim de cada etapa.
