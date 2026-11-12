# Data Model: Estudos de desempenho e estabilidade

App `sgp.studies`.

## studies.Study (`ProtectedModel`)

| Campo | Tipo | Regras |
| --- | --- | --- |
| lineage | UUID | mesma em todas as versões |
| version | inteiro ≥ 1 | único por (lineage, version) |
| project | FK `projects.Project` | |
| study_type | FK `vocab.Term` (`tipo-estudo`) | com perfil de cálculo (contrato `perfis-calculo.md`) |
| title | texto | |
| subdocument / topic_key | FK `subdocuments.Subdocument` (RAPD ou Validação do projeto), chave do tópico | opcional |
| status | `editing`, `locked` | bloqueado na aprovação do subdocumento |
| rounding | `half_even`, `half_up`, `truncate` | padrão `half_even` |
| places / fine_places | inteiro | padrões 2 e 4 |
| ci_method | `clopper_pearson`, `wilson` | padrão Clopper-Pearson |
| cutoff | decimal, nulo | só no tipo `cut-off` |
| criteria | JSON | `[{"metrica", "comparacao", "limite"}]`; não muda depois da primeira linha |
| rows | JSON | linhas numeradas pelo sistema (contrato) |
| results | JSON | calculado a cada gravação em elaboração; congelado no bloqueio |
| not_applicable / justification | booleano, texto | justificativa obrigatória; exclusivo com linhas |
| version_reason | texto | motivo da nova versão |
| created_by/at, updated_by/at, locked_by/at, row_version | | |

## studies.ImportMapping (`ProtectedModel`)

equipment (único), mapping JSON (`{campo: coluna}`), updated_by/at.

## Vocabulário

Migração de dados em `sgp/vocab` com a lista `tipo-estudo` e os 14 tipos da história 1.
