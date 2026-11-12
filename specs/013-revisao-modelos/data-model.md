# Data Model: Revisão controlada dos modelos

App nova `sgp.revisions`. `kind` = `form` (modelo de formulário, 004) ou `layout` (modelo de layout,
006).

## Campos de revisão (mixin abstrato `revisions.RevisableTemplate`)

Acrescentados a `formtemplates.FormTemplate` e `documents.LayoutTemplate`, com migração:

| Campo | Tipo | Regras |
| --- | --- | --- |
| review_status | `editing`, `submitted` | só vale com `status = draft` |
| revision_reason / revision_impact | texto | obrigatórios no envio |
| submitted_by / submitted_at | | |
| discarded_by / discarded_at / discard_reason | | `status = discarded` |
| approved_hash | char(64) | SHA-256 do conteúdo aprovado (research R4) |

`status` ganha `discarded`. Publicado continua imutável (serviço e gatilhos das features 004 e 006).

## revisions.TemplateStep (`AppendOnlyModel`)

| Campo | Tipo |
| --- | --- |
| kind, template_id, version, family | modelo, versão e família (código do tipo de subdocumento ou alvo do layout) |
| step | `opened`, `submitted`, `returned`, `approved`, `became_current`, `discarded` |
| actor / at | pessoa e data e hora do servidor (vazio em `became_current` pela tarefa diária) |
| comment | motivo, impacto ou comentário da etapa |

## revisions.TemplateSignature (`AppendOnlyModel`)

kind, template_id, version, purpose (`approval`, `retirement`), content_hash, signer, signer_name,
signer_title, meaning (`approved`), signed_at.

## revisions.TemplateRetirement (`ProtectedModel`)

| Campo | Regras |
| --- | --- |
| subdocument_type | FK `vocab.Term`; uma retirada em andamento por tipo |
| status | `requested`, `approved`, `returned` |
| reason, requested_by, requested_at | motivo obrigatório |
| decided_by, decided_at, comment | comentário obrigatório na devolução |
| signature | FK `TemplateSignature` (aprovação) |

## Banco

Gatilhos somente de inclusão em `TemplateStep` e `TemplateSignature`; `apply_db_privileges` sem
UPDATE nelas.
