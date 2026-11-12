# Data Model: Integração com o Sankhya

App `sgp.integrations`.

## integrations.IntegrationMapping (`AppendOnlyModel`)

version (único), yaml, parsed (JSON), note, created_by/at. Versão 1 semeada com os registros e
campos lógicos e as entidades do Sankhya vazias.

## integrations.IntegrationMessage (`ProtectedModel`)

| Campo | Tipo | Regras |
| --- | --- | --- |
| record_type | `projeto`, `documento`, `lote`, `insumo_novo`, `resultado_estudo` | |
| idempotency_key | texto, único | `<registro>:<id>:<versão>` |
| project | FK projeto, nulo | |
| object_type / object_id / object_repr | texto | registro de origem |
| payload | JSON | campos lógicos (contrato registros.md) |
| status | `pending`, `waiting_config`, `sent`, `error` | |
| attempts | inteiro | tentativas de envio |
| last_error | texto | sem credenciais |
| next_attempt_at | data e hora, nulo | espera crescente (1, 2, 4, 8, 16 min) |
| mapping_version | inteiro, nulo | versão usada no envio |
| created_at / sent_at | | |

Eventos: `integration.sent`, `integration.failed`, `integration.reprocessed`,
`integration.exported`, `integration.mapping_published`.

## Configuração (variáveis de ambiente)

`SANKHYA_ENABLED`, `SANKHYA_BASE_URL` (padrão `https://api.sankhya.com.br`), `SANKHYA_CLIENT_ID`,
`SANKHYA_CLIENT_SECRET`, `SANKHYA_X_TOKEN`, `SANKHYA_TIMEOUT`, `INTEGRATION_MAX_ATTEMPTS` (6).
