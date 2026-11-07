# Data Model: Modelos de formulário versionados e subdocumentos

## formtemplates.FormTemplate (`ProtectedModel`)

| Campo | Tipo | Regras |
| --- | --- | --- |
| subdocument_type | FK `vocab.Term` (`tipo-subdocumento`) | |
| form_version | inteiro 1–99 | único por tipo; exibido com 2 dígitos |
| reference | texto (200) | ex.: "PSG 20 - Pesquisa e Desenvolvimento de Produtos" |
| valid_from | data | vigência; a vigente é a publicada mais recente com `valid_from` ≤ hoje |
| status | `draft` Rascunho, `published` Publicado | publicado não muda (serviço e gatilho) |
| definition | JSONB | capa e tópicos (contrato `definicao-modelo.md`), validado pelo JSON Schema |
| created_by / created_at / updated_by / updated_at | | |
| published_by / published_at / published_note | | `published_by` nulo só na carga inicial |
| row_version | inteiro | controle otimista do rascunho |

Unicidade: (subdocument_type, form_version); um só rascunho por tipo.

## subdocuments.Subdocument (`ProtectedModel`)

| Campo | Tipo | Regras |
| --- | --- | --- |
| project | FK `projects.Project` | projeto aberto |
| subdocument_type | FK `vocab.Term` | |
| sequence | inteiro | 1 para todos; Alterações numeradas 1, 2, 3… |
| template | FK `FormTemplate` | versão de modelo usada |
| version | inteiro (2 dígitos) | 01 nesta feature |
| status | `draft` Rascunho, `approved` Aprovado | aprovado não é editado |
| data | JSONB | `{"topics": {...}}` (research R6) |
| unmapped_data | JSONB | o que não coube na migração |
| changed_version / new_version | inteiros, nulos | só Alteração |
| review_requested_by | FK `Subdocument` (Alteração), nulo | marca de revisão |
| review_requested_at | data/hora | |
| created_by / created_at / updated_by / updated_at | | |
| approved_by / approved_at | | aprovação provisória (Gestor de P&D ≠ criador) |
| row_version | inteiro | controle otimista |

Unicidade: (project, subdocument_type, sequence).

## subdocuments.FlowAuthorization (*append-only*)

| Campo | Tipo |
| --- | --- |
| project / subdocument_type | FKs |
| reason | texto |
| authorized_by / authorized_at | Gestor de P&D, data/hora |
| missing_requirement | texto (ex.: "Elaboração de Formulação aprovada") |

## subdocuments.FlowAuthorizationUse (*append-only*)

Uso único da autorização (sem UPDATE na autorização): `authorization` (1:1), `subdocument`
(1:1), `used_at`.

## Listas controladas novas (carga inicial, 05-vocabularios)

`funcionalidade`, `classificacao-teste`, `automacao`, `usuario`, `classificacao-uso`, `filtro`,
`requisito-desempenho` (16), `classe-risco` (I a IV), `disposicao`, `prazo-transferencia`,
`setor-transferencia`.

## projects.Project

Sem coluna nova: a Alteração aprovada incrementa `version` pelo serviço de projetos, com evento.
