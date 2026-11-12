# Data Model: Caderno de laboratório eletrônico

App `sgp.notebook`.

## notebook.NotebookEntry (`ProtectedModel`)

| Campo | Tipo | Regras |
| --- | --- | --- |
| project | FK `projects.Project` | projeto aberto na criação |
| number | inteiro ≥ 1 | sequencial e único por projeto |
| author | FK usuário | quem criou; único que edita e assina |
| created_at | data e hora | do servidor |
| title | texto (300) | obrigatório |
| objective, hypothesis, procedure, results, conclusion | texto | HTML sanitizado (contrato) |
| template | FK `EntryTemplate`, nulo | versão do modelo usada |
| relevant | booleano | exige testemunha |
| relevant_by / relevant_at | FK usuário, data e hora | última marcação |
| status | `open`, `signed`, `witnessed` | derivadas: atrasada, aguardando testemunha |
| signed_at | data e hora, nulo | assinatura do autor |
| search_text | texto | texto puro sem acentos (busca) |
| search_vector | `tsvector` gerado | `to_tsvector('portuguese', search_text)`, índice GIN |
| updated_by / updated_at, row_version | | controle de concorrência |

Gatilho: com `status <> 'open'`, recusa alterar projeto, número, autor, criação, título, textos,
modelo e `search_text`.

## notebook.EntryMaterial (`ProtectedModel`)

entry, kind (`lot`, `material`, `sample`), lot / material / sample (FK para a versão do cadastro,
exatamente uma preenchida), code (copiado), added_by/at, removed_by/at. Gatilho: recusa inclusão ou
alteração quando a entrada não está aberta.

## notebook.EntryAttachment (`ProtectedModel`)

entry, file (FK `files.StoredFile`), inline (imagem colada no texto), added_by/at, removed_by/at.
Mesmo gatilho dos materiais. Política de leitura de arquivo: quem acessa o projeto da entrada.

## notebook.Addendum (`AppendOnlyModel`)

entry, number (sequencial por entrada), text (HTML sanitizado), author, created_at, content_hash,
search_text, search_vector (gerado, índice GIN).

## notebook.NotebookSignature (`AppendOnlyModel`)

entry, addendum (nulo; preenchido na assinatura do adendo), role (`author`, `witness`), signer,
signed_at, content_hash. Únicos: (entry, role) para assinaturas da entrada; uma por adendo.

## notebook.EntryTemplate (`ProtectedModel`)

lineage (UUID), version, is_current, active, name, objective, hypothesis, procedure, results,
conclusion (HTML sanitizado), change_reason, created_by/at. Único: (lineage, version); nome único
entre os vigentes.

## notebook.NotebookLink (`ProtectedModel`)

entry, target_type (`subdocument`, `lot`, `study`), subdocument / lot / study (exatamente uma
preenchida, do mesmo projeto), kind (`related`, `promoted`), attachment (FK `EntryAttachment`, só na
promoção), created_by/at, removed_by/at, removal_reason. Vínculo ativo único por (entrada, alvo,
tipo); vínculo `promoted` não é retirado.

## Configuração

`NOTEBOOK_SIGN_DAYS` (padrão 7, variável de ambiente), `FILE_MAX_MB` da 003.
