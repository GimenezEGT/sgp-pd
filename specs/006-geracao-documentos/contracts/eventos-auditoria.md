# Contrato: eventos de auditoria (feature 006)

Eventos de documento levam `project_id`; `object_type` = `documents.<tipo>` (`subdocument`,
`charter`, `business_plan`) e `object_id` = id do documento. Eventos de modelo de layout levam
`object_type` = `documents.layouttemplate`.

| Código | Rótulo | Valor anterior → novo |
| --- | --- | --- |
| `documents.requested` | Geração de documento pedida | — → `{pedido, formato, versao, oficial}` |
| `documents.generated` | Documento gerado | — → `{pedido, arquivo, formato, versao, situacao, oficial, modelo_formulario, modelo_layout, resumo_conteudo, resumo_arquivo, codigo, igual_a_anterior}` |
| `documents.generation_failed` | Falha na geração de documento (alerta) | — → `{pedido, formato, versao, erro}` |
| `documents.regeneration_mismatch` | Regeneração com conteúdo diferente do arquivado (alerta) | `{resumo_conteudo}` → `{resumo_conteudo}` |
| `documents.frozen` | Conteúdo de geração congelado na aprovação | — → `{versao, modelo_layout, resumo}` |
| `documents.downloaded` | Documento gerado baixado | — → `{arquivo, formato, versao, oficial}` |
| `documents.verification_lookup` | Código de verificação consultado | — → `{codigo, encontrado, com_acesso}` |
| `layouts.draft_created` | Rascunho de modelo de layout criado | — → `{alvo, versao, a_partir_de}` |
| `layouts.draft_updated` | Rascunho de modelo de layout alterado | campos alterados → campos alterados |
| `layouts.published` | Modelo de layout publicado | — → `{alvo, versao, vigencia, resumo}` |

Falha de integridade de arquivo arquivado continua registrada como `files.integrity_failed`
(feature 003), e acesso negado como `auth.permission_denied` (feature 001, `deny_access`).
