# Contrato: eventos de auditoria (feature 004)

Eventos de subdocumento levam `project_id`.

| Código | Rótulo | Valor anterior → novo |
| --- | --- | --- |
| `formtemplates.draft_created` | Rascunho de modelo criado | — → `{tipo, versao, a_partir_de}` |
| `formtemplates.draft_updated` | Rascunho de modelo alterado | campos alterados (metadados e tópicos) |
| `formtemplates.published` | Modelo publicado | — → `{tipo, versao, vigencia}` |
| `subdocuments.created` | Subdocumento criado | — → `{tipo, numero, modelo, versao}` |
| `subdocuments.updated` | Subdocumento alterado | tópicos alterados (antes e depois) |
| `subdocuments.flow_authorized` | Criação fora da ordem autorizada | — → `{tipo, falta}`; motivo em `reason` |
| `subdocuments.derived_refreshed` | Linhas derivadas atualizadas | linhas antes → depois |
| `subdocuments.template_migrated` | Subdocumento migrado de modelo | `{modelo}` → `{modelo, nao_migrados}`; motivo em `reason` |
| `subdocuments.approved` | Subdocumento aprovado (confirmação) | — → `{versao, modelo}` |
| `subdocuments.review_requested` | Subdocumento marcado para revisão | — → `{alteracao}` |
| `projects.version_changed` | Versão do projeto alterada | `{versao}` → `{versao}`; Alteração em `reason` |
