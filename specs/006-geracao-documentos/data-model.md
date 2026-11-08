# Data Model: Geração de documentos no padrão da empresa

App `sgp.documents`. `kind` usa os tipos da feature 005: `subdocument`, `charter`, `business_plan`.

## documents.LayoutTemplate (`ProtectedModel`)

| Campo | Tipo | Regras |
| --- | --- | --- |
| target | `subdocument`, `charter`, `business_plan` | a que documentos se aplica |
| version | inteiro ≥ 1 | único por (target, version); exibido com 2 dígitos |
| valid_from | data | início da vigência |
| status | `draft`, `published` | um rascunho por alvo; publicado é imutável (serviço e trigger) |
| definition | JSONB | contrato `modelo-layout.md`, validado por JSON Schema |
| logo | FK `files.StoredFile`, nulo | nulo = faixa padrão (arquivo estático, SHA-256 conferido) |
| note | texto | observação da publicação |
| created_by/at, updated_by/at, published_by/at, row_version | | concorrência otimista como no modelo de formulário |

Vigente de um alvo numa data: publicado mais recente com `valid_from` ≤ data. Migração de dados cria
a versão 01 publicada de cada alvo com os padrões da prova de layout (vigência 2020-01-01).

## documents.LayoutBinding (`AppendOnlyModel`)

| Campo | Tipo | Regras |
| --- | --- | --- |
| kind, object_id, version | | único por (kind, object_id, version) |
| layout | FK `LayoutTemplate` publicado | vigente quando a versão do documento começou |
| bound_at | data e hora | |

## documents.FrozenRendering (`AppendOnlyModel`)

| Campo | Tipo | Regras |
| --- | --- | --- |
| kind, object_id, version | | único por (kind, object_id, version) |
| project | FK `projects.Project` | |
| layout | FK `LayoutTemplate` | layout da versão (do `LayoutBinding`) |
| content | JSONB | contrato `conteudo-renderizacao.md`, com assinaturas e data de aprovação |
| content_hash | char(64) | SHA-256 do JSON canônico (`signatures.canonical`) |
| created_at | data e hora | na aprovação (ou na primeira geração oficial, para aprovações anteriores à 006) |

## documents.GenerationRequest (`ProtectedModel`)

| Campo | Tipo | Regras |
| --- | --- | --- |
| kind, object_id, project, version | | documento e versão no momento do pedido |
| format | `pdf`, `docx` | |
| official | booleano | PDF de versão aprovada |
| status | `queued`, `running`, `done`, `failed` | transições: queued → running → done ou failed |
| requested_by / requested_at | | |
| started_at / finished_at | | |
| error | texto | mensagem compreensível da falha |
| result | FK `GeneratedDocument`, nulo | preenchido quando `done` |

Só um pedido `queued` ou `running` por (kind, object_id, version, format): restrição única parcial.

## documents.GeneratedDocument (`AppendOnlyModel`)

| Campo | Tipo | Regras |
| --- | --- | --- |
| request | FK `GenerationRequest` | |
| kind, object_id, project, version | | |
| document_status | situação do documento na geração | `draft`, `in_review`, `returned`, `approved` |
| format, official | | |
| form_template | FK `formtemplates.FormTemplate`, nulo | nulo no TAP e no Plano de Negócios |
| layout | FK `LayoutTemplate` | |
| data_version | inteiro | `row_version` do documento usado (rascunho) |
| file | FK `files.StoredFile` | arquivo arquivado (conteúdo conferido a cada leitura) |
| content_hash | char(64) | antes do selo (PDF) ou do DOCX normalizado |
| file_hash | char(64) | igual a `file.sha256` |
| verification_code | char(19), em branco | só no PDF oficial; índice para consulta |
| same_as_first | booleano, nulo | oficial: resumo do conteúdo igual ao da primeira geração da versão |
| generated_by / generated_at | | |

## files.StoredFile (feature 003)

Novo tipo `docx` em `sgp.files.storage.KINDS` (`application/vnd.openxmlformats-officedocument.wordprocessingml.document`),
fora dos tipos aceitos em upload; nova função `store_bytes(data, *, name, kind, by)` para arquivos
gerados. Política de acesso `generated_document` registrada em `sgp.files.access`.

## Banco

- Triggers: `LayoutTemplate` publicado não muda (como `formtemplates` 0002); `LayoutBinding`,
  `FrozenRendering` e `GeneratedDocument` somente de inclusão (`immutable_trigger_sql`).
- `apply_db_privileges`: sem UPDATE/DELETE nas tabelas somente de inclusão; sem DELETE nas demais.
