# Data Model: Revisão, versões e assinatura eletrônica

## signatures.ApprovedVersion (*append-only*)

| Campo | Tipo | Regras |
| --- | --- | --- |
| kind | `subdocument`, `charter`, `business_plan` | |
| object_id | inteiro | |
| project | FK `projects.Project` | |
| version | inteiro ≥ 1 | único por (kind, object_id) |
| content | JSONB | conteúdo canônico (contrato `conteudo-canonico.md`) |
| content_hash | char(64) | SHA-256 do JSON canônico |
| approved_by / approved_at | | |

## signatures.Signature (*append-only*)

| Campo | Tipo |
| --- | --- |
| kind / object_id / version / project | |
| content_hash | char(64) do conteúdo assinado |
| meaning | `elaborated` Elaborado, `reviewed` Revisado, `approved` Aprovado |
| signer / signer_name / signer_title | pessoa, nome e função no momento |
| signed_at | data e hora do servidor |
| delegation | FK `ApprovalDelegation`, nulo |

## signatures.SignatureAttempt (*append-only*) e SignatureLock

- `SignatureAttempt`: user, success, reason, at.
- `SignatureLock` (`ProtectedModel`): user, created_at, expires_at.

## signatures.ReviewComment (*append-only*)

kind, object_id, version, project, author, action (`returned`), text, created_at.

## signatures.ApprovalDelegation (`ProtectedModel`)

delegator, delegate, starts_on, ends_on (≤ 30 dias), reason, created_at, ended_at, ended_by,
end_reason.

## Alterações em modelos existentes

- `subdocuments.Subdocument.status`: + `in_review` Em revisão, `returned` Devolvido.
- `projects.ProjectCharter` e `projects.BusinessPlan`: + `doc_status` (rascunho, em revisão,
  devolvido, aprovado) e `doc_version` (padrão 1).
