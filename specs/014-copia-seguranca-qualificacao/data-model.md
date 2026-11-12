# Data Model: Cópia de segurança, restauração e qualificação do sistema

## operations.BackupRun (`ProtectedModel`)

| Campo | Tipo | Regra |
| --- | --- | --- |
| kind | `scheduled` (agendada) ou `manual` (pedida) | |
| status | `running`, `success`, `failed` | uma `running` por vez (bloqueio consultivo) |
| label | texto | nome da pasta `AAAAMMDD-HHMMSS` no destino |
| started_at, finished_at | data e hora (UTC) | |
| system_version | texto | versão + commit |
| database_size, database_sha256 | inteiro, texto | do `banco.dump` |
| server_version | texto | versão do PostgreSQL |
| table_counts | JSON | tabela → linhas no instantâneo |
| audit_head_seq, audit_head_hash | inteiro, texto | último evento da trilha no instantâneo |
| files_total, files_new, files_bytes | inteiros | arquivos do instantâneo e novos no acervo |
| manifest_sha256 | texto | resumo do `manifesto.json` |
| monthly | booleano | primeira cópia bem-sucedida do mês (não é removida) |
| removed_at | data e hora, nulo | remoção pela retenção (os arquivos da pasta saem; o registro fica) |
| error | texto | motivo da falha |
| requested_by | pessoa, nulo | quem pediu a cópia manual |

## operations.RestoreTest (`ProtectedModel`)

| Campo | Tipo | Regra |
| --- | --- | --- |
| backup | BackupRun, nulo | cópia testada (nula se não havia cópia) |
| kind | `scheduled` ou `manual` | |
| status | `running`, `passed`, `failed` | um teste por vez |
| started_at, finished_at | data e hora | |
| checks | JSON | lista `{codigo, descricao, aprovado, detalhe}` (C1 a C6) |
| error | texto | motivo da reprovação |
| requested_by | pessoa, nulo | |

## operations.QualificationRun (`AppendOnlyModel`)

| Campo | Tipo | Regra |
| --- | --- | --- |
| kind | `installation` (IQ) ou `operation` (OQ) | |
| channel | `command` (linha de comando) ou `screen` (tela) | |
| executed_by | pessoa | IQ: Administrador; OQ: Administrador ou Garantia da Qualidade |
| started_at, finished_at | data e hora | |
| system_version | texto | versão + commit |
| items | JSON | lista `{codigo, descricao, resultado, detalhe}`; resultado `aprovado`, `reprovado` ou `nao_aplicavel` |
| passed | booleano | nenhum item reprovado |
| report | StoredFile (PDF) | relatório guardado com SHA-256 |

## Eventos da trilha

`operations.backup_completed`, `operations.backup_failed`, `operations.backup_removed`,
`operations.backup_requested`, `operations.restore_tested`, `operations.restore_requested`,
`operations.backup_stale`, `operations.qualification_executed`,
`operations.qualification_requested`, `operations.report_downloaded`,
`operations.access_review_exported`.

## Migrações

`operations.0001_initial` (três modelos) e `operations.0002_trigger` (gatilho de imutabilidade em
`operations_qualificationrun`).
