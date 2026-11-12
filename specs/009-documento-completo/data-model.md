# Data Model: Documento completo do projeto

App `sgp.fulldoc`.

## fulldoc.FullDocumentRequest (`ProtectedModel`)

| Campo | Tipo | Regras |
| --- | --- | --- |
| project | FK `projects.Project` | |
| project_version | inteiro | versão do projeto no pedido |
| options | JSON | `{"caderno": "resumido" ou "completo", "historico_versoes": booleano}` |
| with_financials | booleano | quem pediu vê dados financeiros |
| status | `queued`, `running`, `done`, `failed` | um pedido ativo por projeto |
| progress / step | inteiro 0–100, texto | etapa atual (montagem, renderização, selo, arquivo) |
| requested_by / requested_at, started_at, finished_at | | |
| error | texto | mensagem amigável da falha |
| result | FK `FullDocument`, nulo | gerado ou reaproveitado |
| reused | booleano | resultado reaproveitado |

## fulldoc.FullDocument (`AppendOnlyModel`)

| Campo | Tipo | Regras |
| --- | --- | --- |
| project, project_version | | |
| options | JSON | as do pedido |
| with_financials | booleano | baixa só quem vê dados financeiros quando verdadeiro |
| official | booleano | sem pendências |
| pending | JSON | lista de pendências na geração |
| composition_hash | texto (64) | resumo da composição (research R10) |
| layout | FK `documents.LayoutTemplate` | layout vigente usado |
| file | FK `files.StoredFile` | PDF (com selo, se oficial) |
| content_hash / file_hash | texto (64) | PDF antes do selo / arquivo guardado |
| verification_code | texto (19) | só oficial; indexado |
| pages | inteiro | número de páginas |
| generated_by / generated_at | | |

Eventos: `fulldoc.requested`, `fulldoc.generated`, `fulldoc.reused`, `fulldoc.failed`,
`fulldoc.downloaded`.
