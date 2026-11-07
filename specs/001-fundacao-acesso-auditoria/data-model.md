# Data Model: Fundação — acesso, perfis e trilha de auditoria

Convenções: identificadores em inglês; rótulos em pt-BR entre aspas. Toda data/hora é `timestamptz`
gravada em UTC pelo servidor. Nenhuma tabela de negócio admite DELETE (modelos `ProtectedModel`);
as marcadas *append-only* também não admitem UPDATE (`AppendOnlyModel`).

## accounts.User — "Pessoa"

| Campo | Tipo | Regras |
| --- | --- | --- |
| id | bigint PK | |
| username | varchar(150), único | login de rede normalizado em minúsculas |
| full_name | varchar(255) | `displayName` do AD; se vazio, nome + sobrenome |
| first_name / last_name | varchar(150) | `givenName` / `sn` |
| email | varchar(254) | `mail` |
| job_title | varchar(255) | "Função" (`title`); usada depois nas assinaturas |
| is_active | boolean | desativação lógica; nunca excluída |
| password | varchar(128) | sempre inutilizável (`set_unusable_password`); a senha nunca é guardada |
| created_at | timestamptz | primeiro login ou pré-cadastro do administrador inicial |
| last_login | timestamptz | atualizado a cada login aceito |

Regras: criado no primeiro login aceito (FR-002); atributos de rede atualizados a cada login, com
evento `accounts.user_updated` (valor anterior e novo só dos campos alterados). O Administrador
desativa e reativa a pessoa com motivo (FR-026), também com `accounts.user_updated`; o último
Administrador ativo não pode ser desativado.

## accounts.ProfileAssignment — "Concessão de perfil"

| Campo | Tipo | Regras |
| --- | --- | --- |
| id | bigint PK | |
| user | FK User (PROTECT) | |
| profile | varchar(20) | `ADMIN`, `RD_MANAGER`, `PROJECT_LEADER`, `ANALYST`, `QUALITY`, `READER` |
| source | varchar(20) | `manual` ou `network_group` |
| source_group | varchar(500) | DN do grupo quando `source = network_group` |
| granted_at | timestamptz | |
| granted_by | FK User null | nulo = sistema (sincronização ou implantação) |
| grant_reason | text | obrigatório |
| approval_reference | varchar(500) | obrigatório na concessão manual |
| revoked_at | timestamptz null | preenchido na revogação |
| revoked_by | FK User null | |
| revoke_reason | text | obrigatório na revogação |
| revoke_approval_reference | varchar(500) | obrigatório na revogação manual; "Saída do grupo da rede" na sincronização |

Restrições: índice único parcial `(user, profile) WHERE revoked_at IS NULL` (no máximo uma concessão
ativa por perfil). Estados: ativa → revogada (definitivo). Não se revoga o último `ADMIN` ativo
(FR-012). A sincronização de grupos só revoga concessões `network_group`.

Perfis e rótulos:

| Código | Rótulo | Acesso a todos os projetos |
| --- | --- | --- |
| ADMIN | "Administrador do sistema" | sim |
| RD_MANAGER | "Gestor de P&D" | sim |
| PROJECT_LEADER | "Líder de projeto" | não (só como membro) |
| ANALYST | "Analista/Pesquisador" | não (só como membro) |
| QUALITY | "Qualidade/Assuntos Regulatórios" | sim |
| READER | "Leitor" | não (só como membro) |

## accounts.AccessRequest — "Solicitação de acesso"

| Campo | Tipo | Regras |
| --- | --- | --- |
| id | bigint PK | |
| user | FK User | quem pede |
| justification | text | obrigatória |
| created_at | timestamptz | |
| status | varchar(10) | `pending` → `granted` ou `rejected` (definitivo) |
| decided_at / decided_by / decision_reason | timestamptz / FK User / text | obrigatórios na decisão |

## accounts.LoginAttempt — "Tentativa de login" (*append-only*)

| Campo | Tipo | Regras |
| --- | --- | --- |
| id | bigint PK | |
| username | varchar(150) | como digitado, normalizado |
| user | FK User null | quando a pessoa existe |
| attempted_at | timestamptz | |
| result | varchar(12) | `success`, `failure`, `blocked`, `unavailable` |
| ip_address | varchar(45) | |

## accounts.LoginLockout — "Bloqueio de login"

| Campo | Tipo | Regras |
| --- | --- | --- |
| id | bigint PK | |
| username | varchar(150) | |
| started_at | timestamptz | |
| expires_at | timestamptz | `started_at + LOGIN_LOCKOUT_MINUTES` |
| failure_count | int | tentativas que geraram o bloqueio |
| released_at / released_by / release_reason | timestamptz / FK User / text | desbloqueio manual (FR-007) |

Regra: bloqueio ativo = `released_at IS NULL AND expires_at > agora`. Falhas contadas = tentativas
`failure` depois do mais recente entre: último `success`, fim do último bloqueio e desbloqueio
manual. Ao atingir `LOGIN_MAX_FAILURES`, cria-se o bloqueio. Tentativas `blocked` e `unavailable`
não contam.

## audit.AuditEvent — "Evento de auditoria" (*append-only*, encadeado)

| Campo | Tipo | Regras |
| --- | --- | --- |
| seq | bigint PK | 1, 2, 3… sem lacunas, atribuído sob trava |
| occurred_at | timestamptz | horário do servidor, obtido depois da trava |
| actor | FK User null (PROTECT, com restrição de chave estrangeira no banco) | nulo = "sistema" ou "anônimo" (`actor_username` diz qual); pessoas nunca são apagadas, então a FK não impede a trilha |
| actor_username | varchar(150) | instantâneo do login ou `sistema` |
| event_type | varchar(64), indexado | catálogo em `contracts/eventos-auditoria.md` |
| object_type | varchar(100) | ex.: `accounts.user` |
| object_id | varchar(64) | |
| object_repr | varchar(255) | descrição legível no momento do evento |
| project_id | bigint null, indexado | preenchido pelas features com projeto |
| old_value / new_value | jsonb null | só texto, inteiro, booleano, nulo, listas e objetos |
| reason | text | motivo, quando houver |
| ip_address | varchar(45) | origem da requisição |
| prev_hash | char(64) | hash do evento anterior; 64 zeros no primeiro |
| hash | char(64), único | SHA-256 do JSON canônico |

Índices: `occurred_at`, `(actor, occurred_at)`, `(event_type, occurred_at)`, `(project_id,
occurred_at)`. Trigger `audit_event_immutable` recusa UPDATE e DELETE.

## audit.ChainVerification — "Verificação de integridade" (*append-only*)

| Campo | Tipo | Regras |
| --- | --- | --- |
| id | bigint PK | |
| started_at / finished_at | timestamptz | |
| trigger | varchar(10) | `scheduled` ou `manual` |
| triggered_by | FK User null | quem pediu, na verificação manual |
| events_checked | bigint | |
| status | varchar(10) | `intact` ou `broken` |
| head_seq / head_hash | bigint / char(64) | ponto de controle: último evento verificado |
| breaks | jsonb | lista `{seq, kind, detail}`; `kind` ∈ `content_altered`, `chain_broken`, `sequence_gap`, `checkpoint_missing`, `checkpoint_mismatch` |

O alerta de quebra (FR-022) usa a verificação mais recente.

## Privilégios do papel da aplicação (`sgp_app`)

| Tabela | SELECT | INSERT | UPDATE | DELETE |
| --- | --- | --- | --- | --- |
| `audit_auditevent`, `audit_chainverification`, `accounts_loginattempt` | sim | sim | não | não |
| demais tabelas de negócio | sim | sim | sim | não |
| `django_session` | sim | sim | sim | sim |

TRUNCATE nunca é concedido. O papel dono (`sgp_owner`) é usado só por migrações, pelo comando de
privilégios e pelos testes.
