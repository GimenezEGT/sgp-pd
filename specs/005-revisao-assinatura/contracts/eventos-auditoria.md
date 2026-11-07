# Contrato: eventos de auditoria (feature 005)

Todos levam `project_id`; `object_type` = `signatures.<tipo>` e `object_id` = id do documento.

| Código | Rótulo | Valor anterior → novo |
| --- | --- | --- |
| `signatures.submitted` | Documento enviado para revisão | `{situacao}` → `{situacao, versao, resumo}` |
| `signatures.signed` | Documento assinado | — → `{versao, significado, resumo, delegacao}` |
| `signatures.failed` | Falha de senha na assinatura | — → `{tentativas_seguidas}` |
| `signatures.blocked` | Assinatura bloqueada por falhas (alerta) | — → `{bloqueado_ate}` |
| `signatures.returned` | Documento devolvido na revisão | `{situacao}` → `{situacao}`; comentário em `reason` |
| `signatures.approved` | Documento aprovado com assinatura | — → `{versao, resumo}` |
| `signatures.new_version` | Nova versão de documento | `{versao}` → `{versao}`; motivo em `reason` |
| `signatures.verified` | Integridade do documento verificada | — → `{integro, problemas}` |
| `signatures.delegation_created` / `signatures.delegation_ended` | Delegação de aprovação criada / encerrada | `{delegado, inicio, fim}`; motivo em `reason` |
