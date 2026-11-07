# Contrato: catálogo de eventos e formato do hash

## Catálogo (feature 001)

| Código | Rótulo | Objeto | Valor anterior → novo |
| --- | --- | --- | --- |
| `auth.login_succeeded` | Login aceito | pessoa | — |
| `auth.login_failed` | Login recusado | login digitado | — |
| `auth.login_blocked` | Tentativa durante bloqueio | login digitado | — |
| `auth.lockout_started` | Login bloqueado por tentativas | bloqueio | — → `{falhas, expira_em}` |
| `auth.lockout_released` | Login desbloqueado | bloqueio | `{expira_em}` → `{liberado_em}` |
| `auth.auth_unavailable` | Serviço de autenticação indisponível | login digitado | — |
| `auth.logout` | Logout | pessoa | — |
| `auth.session_expired` | Sessão encerrada por inatividade | pessoa | `{ultimo_acesso}` → — |
| `auth.permission_denied` | Acesso negado | rota | — → `{rota, metodo}` |
| `accounts.user_created` | Cadastro de pessoa criado | pessoa | — → atributos |
| `accounts.user_updated` | Cadastro de pessoa alterado | pessoa | campos alterados |
| `accounts.profile_granted` | Perfil concedido | concessão | perfis ativos antes → depois |
| `accounts.profile_revoked` | Perfil revogado | concessão | perfis ativos antes → depois |
| `accounts.access_requested` | Acesso solicitado | solicitação | — |
| `accounts.access_request_decided` | Solicitação de acesso decidida | solicitação | `pending` → `granted` ou `rejected` |
| `audit.exported` | Trilha exportada | — | — → `{formato, filtros, eventos}` |
| `audit.chain_verified` | Integridade da trilha verificada | verificação | — → `{situacao, eventos, ultimo_seq, quebras}` |

As features seguintes acrescentam códigos com o prefixo da app (`projects.`, `catalog.` …). O motivo
informado pelo usuário vai no campo `reason`.

## Campos e hash

Cada evento é serializado para o hash como JSON canônico, por exemplo:

```text
{"actor_id":12,"actor_username":"ana.silva","event_type":"accounts.profile_granted","ip_address":"10.0.0.15","new_value":{"perfis":["ANALYST"]},"object_id":"7","object_repr":"Analista/Pesquisador - ana.silva","object_type":"accounts.profileassignment","occurred_at":"2026-11-07T13:05:22.123456+00:00","old_value":{"perfis":[]},"prev_hash":"<64 hex>","project_id":null,"reason":"<motivo>","seq":42}
```

- chaves em ordem alfabética, separadores `,` e `:` sem espaços, UTF-8 sem escape de não ASCII;
- `occurred_at` em UTC, ISO 8601 com microssegundos e `+00:00`;
- `old_value` e `new_value` contêm só texto, inteiros, booleanos, nulos, listas e objetos (decimais,
  datas e UUIDs viram texto antes da gravação);
- `hash = SHA-256(utf8(json))` em hexadecimal minúsculo; o primeiro evento usa `prev_hash` com 64
  zeros.

A verificação recalcula o hash de cada evento, confere `prev_hash` com o hash do evento anterior,
confere a sequência sem lacunas e confronta o último ponto de controle registrado.
