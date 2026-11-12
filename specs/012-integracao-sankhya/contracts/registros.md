# Contrato: registros do modelo lógico (feature 012)

Campos lógicos de cada registro (contexto `docs/contexto/07-integracao-sankhya.md`), na mensagem e
na exportação de contingência. O mapeamento liga cada campo lógico a um campo do Sankhya; a chave
de idempotência vai no campo indicado como `chave`.

| Registro | Gerado quando | Campos lógicos |
| --- | --- | --- |
| projeto | projeto aprovado (`projects.approved`) | codigo_projeto, nome, produto, tecnologia, orgao, classe_risco, lider, situacao, versao_projeto, data_abertura |
| documento | subdocumento aprovado com assinatura (`signatures.approved`) | codigo_projeto, tipo_subdocumento, versao_documento, versao_formulario, referencia_psg, data_aprovacao, elaborador, aprovador, resumo_conteudo, pdf_sha256, pdf_codigo_verificacao |
| lote | lote citado num subdocumento aprovado | codigo_lote, tipo, codigo_projeto, data_fabricacao, data_validade, local, responsavel |
| insumo_novo | Saída aprovada com insumo novo (solicitação de cadastro) | descricao, tipo, fabricante, lote_fabricante, certificado_nome, certificado_sha256, codigo_projeto, situacao (`solicitado`) |
| resultado_estudo | estudo bloqueado pela aprovação do subdocumento | codigo_projeto, tipo_estudo, titulo, versao, criterio, resultado, conclusao, documento_origem |

Chave de idempotência: `<registro>:<id do registro de origem>:<versão>`; o reenvio grava o mesmo
registro (o `saveRecord` inclui ou altera pela chave primária).

Consulta de produto: entidade e campos (código, descrição, unidade, situação) também vêm do
mapeamento.
