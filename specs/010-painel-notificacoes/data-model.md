# Data Model: Painel do gestor e notificações

App `sgp.dashboard` (painel, linha do tempo, pendências, exportação) e `sgp.notifications`
(preferências, notificações e envio).

## notifications.NotificationPreference (`ProtectedModel`)

| Campo | Tipo | Regras |
| --- | --- | --- |
| user | FK usuário | |
| kind | `returned`, `approved`, `stalled` | `pending_signature` não aparece: não pode ser desligada |
| enabled | booleano | padrão ligado |
| updated_at | data e hora | |

Único por (user, kind).

## notifications.Notification (`ProtectedModel`)

| Campo | Tipo | Regras |
| --- | --- | --- |
| user | FK usuário | destinatário |
| kind | `returned`, `approved`, `stalled`, `pending_signature` | |
| object_type / object_id / object_repr | texto | registro de origem (documento, entrada do caderno) |
| project | FK projeto, nulo | |
| subject / body | texto | e-mail em português |
| dedup_key | texto | evita repetir o mesmo lembrete no mesmo dia |
| status | `pending`, `sent`, `failed`, `skipped` | `skipped`: preferência desligada ou sem e-mail |
| attempts | inteiro | até 3 |
| created_at / sent_at | | |
| error | texto | |

Único por `dedup_key`. Eventos: `notifications.sent`, `notifications.failed`,
`notifications.skipped`, `notifications.preference_changed`, `dashboard.exported`.

## Índices dedicados

- `projects_milestone (project_id, planned_date)` para marcos por projeto;
- `signatures_approvedversion (kind, project_id)` para versões aprovadas por projeto;
- `notebook_notebookentry (project_id, status, created_at)` para entradas atrasadas.

## Configuração

`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`,
`DEFAULT_FROM_EMAIL`, `EMAIL_BACKEND` (desenvolvimento: arquivo), `SITE_URL` (endereço nos
e-mails), `NOTIFICATION_DIGEST_HOUR` (7), `DASHBOARD_CACHE_SECONDS` (300), `CACHE_URL`.
