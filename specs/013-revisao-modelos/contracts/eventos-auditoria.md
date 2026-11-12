# Contrato: eventos de auditoria (feature 013)

`object_type` = `formtemplates.formtemplate` ou `documents.layouttemplate`; `object_id` = versão.

| Código | Rótulo | Valor anterior → novo |
| --- | --- | --- |
| `formtemplates.draft_created` / `layouts.draft_created` (004/006) | Abertura da revisão | — → `{versao, a_partir_de}` |
| `formtemplates.draft_updated` / `layouts.draft_updated` (004/006) | Alteração do rascunho | campos alterados |
| `templates.submitted` | Revisão de modelo enviada para aprovação | — → `{versao, motivo, impacto, mudancas}` |
| `templates.returned` | Revisão de modelo devolvida | `{situacao}` → `{situacao}`; comentário em `reason` |
| `templates.approved` | Revisão de modelo aprovada com assinatura | — → `{versao, vigencia, resumo}` |
| `formtemplates.published` / `layouts.published` (004/006) | Publicação | — → `{versao, vigencia}` |
| `templates.became_current` | Versão de modelo entrou em vigência | — → `{versao, anterior}` |
| `templates.discarded` | Revisão de modelo descartada | — → `{versao}`; motivo em `reason` |
| `templates.verified` | Integridade de versão de modelo verificada | — → `{integro, problemas}` |
| `templates.retirement_requested` | Retirada de modelo pedida | — → `{tipo}`; motivo em `reason` |
| `templates.retirement_approved` | Retirada de modelo aprovada com assinatura | — → `{tipo, resumo}` |
| `templates.retirement_returned` | Retirada de modelo devolvida | comentário em `reason` |
