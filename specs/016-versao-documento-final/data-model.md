# Data Model: Versionamento do documento final do projeto

## fulldoc.FinalDocumentVersion (`AppendOnlyModel`, gatilho de imutabilidade)

| Campo | Tipo | Regra |
| --- | --- | --- |
| project | Projeto | |
| number | inteiro | sequencial por projeto, a partir de 1; único com `project` |
| created_at | data e hora | da aprovação (na reconstrução, a da aprovação original) |
| approved_by | pessoa, nulo | quem aprovou a mudança (nulo na recomposição sem pessoa) |
| reason | `approval`, `recomposition`, `reconstruction` | |
| changes | JSON | lista `{tipo, id, parte, de, para, aprovada_em}`; `de` nulo na primeira aprovação da parte |
| composition | JSON | lista `{tipo, id, parte, versao, aprovada_em, resumo}` na ordem do documento |
| composition_hash | texto (64) | SHA-256 do JSON canônico da composição |

## fulldoc.FullDocument (alteração)

| Campo | Tipo | Regra |
| --- | --- | --- |
| final_version | FinalDocumentVersion, nulo | versão do documento final representada (nulo nos gerados antes da 016) |

## Eventos

`fulldoc.version_created` (nova versão: número, motivo, mudanças, resumo da composição). Para as
versões reconstruídas, gravado pelo "sistema" logo depois das migrações (sinal `post_migrate`),
com a data e o aprovador originais no valor (`aprovada_em`, `aprovada_por`).

## Migrações

`0003_final_document_version` (modelo e campo), `0004_final_version_trigger` (imutabilidade),
`0005_rebuild_history` (reconstrução das aprovações registradas; reversão sem efeito).
