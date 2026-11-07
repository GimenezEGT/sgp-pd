# 07 — Integração com o Sankhya

## O que já se sabe (documentação pública da Sankhya, conferida em novembro de 2026)

- Toda integração passa pelo API Gateway. Conexão direta ao banco, chamadas fora do gateway ou qualquer rota que o contorne não são aceitas pela Sankhya.
- Autenticação OAuth 2.0 client credentials: `POST https://api.sankhya.com.br/authenticate`, com `client_id`, `client_secret` e `grant_type=client_credentials` no corpo (form data) e o header `X-Token`. O `client_id` e o `client_secret` são gerados na Área do Desenvolvedor; o `X-Token` vem da tela "Configurações Gateway" do Sankhya Om. A resposta traz um token JWT.
- O login antigo por usuário e senha está marcado como legado/descontinuado, e o modelo antigo de appkey + token foi substituído pelo OAuth.
- O token fica ligado a um usuário do Sankhya Om; as permissões desse usuário limitam o que a integração pode fazer.
- Padrão das chamadas: `https://api.sankhya.com.br/gateway/v1/{modulo}/service.sbr?serviceName={servico}&outputType=json`, com `Authorization: Bearer {token}`. A documentação usa o ambiente de testes (Playground) nos exemplos; em produção só muda a URL.
- Módulo `mge` para cadastros gerais; `mgecom` para movimentos comerciais. Serviço de um módulo não funciona no outro.
- Leitura: `CRUDServiceProvider.loadRecords` (e `DatasetSP.loadRecords`). Gravação: `CRUDServiceProvider.saveRecord`; não se usa PUT, e o POST inclui ou altera conforme a chave primária exista.
- No dicionário de dados (TDDTAB, TDDCAM, TDDINS), tabelas e campos criados pela empresa são marcados como adicionais.

O formato exato do corpo de `saveRecord` e `loadRecords` está na referência "Incluir e Alterar Dados" e "Como consultar dados?" do portal do desenvolvedor; confirme com a consultoria antes do `/speckit-plan` da feature 012.

## O que pedir à TI e à consultoria Sankhya

1. Acesso ao ambiente de testes e ao de produção; `client_id`, `client_secret` e `X-Token`.
2. Usuário do Sankhya que representará o SGP-P&D e as permissões dele.
3. Criação das tabelas adicionais para os registros de P&D (proposta abaixo) e das instâncias correspondentes.
4. Nomes das entidades/instâncias a usar em `loadRecords` e `saveRecord`.
5. Entidade e campos do cadastro de produtos/insumos para consulta (código, descrição, unidade, situação).
6. Regra para nova matéria-prima ou embalagem: cadastro direto pelo sistema ou solicitação para o cadastro.
7. Se o ERP guarda o PDF oficial ou só a referência a ele.
8. Limites de requisição e janelas de manutenção.

## Proposta de dados a gravar (modelo lógico, a ajustar com a consultoria)

| Registro | Campos |
| --- | --- |
| Projeto P&D | código do projeto, nome, produto, tecnologia, órgão, classe de risco, regime, líder, status, versão do projeto, data de abertura, data de encerramento |
| Documento P&D | código do projeto, tipo de subdocumento, versão do documento, versão do formulário, referência PSG, data de aprovação, elaborador, aprovador, hash SHA-256 do PDF, identificador do PDF no SGP-P&D |
| Lote P&D | código do lote, tipo (piloto, validação), produto, fabricação, validade, local, responsável |
| Insumo novo | descrição, tipo (matéria-prima, embalagem), fabricante, especificação, certificado, projeto de origem, situação da solicitação |
| Resultado de estudo | código do projeto, tipo de estudo, critério de aceitação, resultado calculado, conclusão, documento de origem |

## Contingência (antes da API)

Exportar os mesmos registros em CSV (UTF-8, separador ";", vírgula decimal) e XLSX, um arquivo por registro da tabela acima, e em JSON com o envelope próprio do SGP-P&D: `{"entidade": "...", "gerado_em": "...", "registros": [...]}`. Esse layout é do SGP-P&D, não da Sankhya, e serve para importação assistida.
