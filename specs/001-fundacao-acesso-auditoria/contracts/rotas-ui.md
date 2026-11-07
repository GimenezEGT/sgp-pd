# Contrato: telas e rotas (feature 001)

Todas as rotas exigem pessoa autenticada, exceto as marcadas "anônimo". Pessoa sem perfil ativo só
acessa `/solicitar-acesso/` e `/sair/`; as demais respondem com redirecionamento para
`/solicitar-acesso/` e evento `auth.permission_denied`. Falta do perfil exigido responde 403 com a
página "Acesso negado" e o mesmo evento. Requisições HTMX (`HX-Request: true`) recebem só o
fragmento da tabela.

| Rota | Método | Perfis | Comportamento | Eventos |
| --- | --- | --- | --- | --- |
| `/entrar/` | GET, POST | anônimo | formulário de login; o POST confere bloqueio, autentica no AD, registra a tentativa e encaminha | `auth.login_succeeded`, `auth.login_failed`, `auth.login_blocked`, `auth.lockout_started`, `auth.auth_unavailable`, `accounts.user_created`, `accounts.user_updated`, `accounts.profile_granted`/`accounts.profile_revoked` (sincronização) |
| `/sair/` | POST | autenticado | encerra a sessão | `auth.logout` |
| `/solicitar-acesso/` | GET, POST | autenticado | instruções (`ACCESS_REQUEST_INSTRUCTIONS`), formulário com justificativa obrigatória e histórico das próprias solicitações | `accounts.access_requested` |
| `/` | GET | qualquer perfil | página inicial com os perfis da pessoa e os atalhos permitidos | — |
| `/administracao/pessoas/` | GET | ADMIN | lista com busca por login ou nome e perfis ativos | — |
| `/administracao/pessoas/<id>/` | GET | ADMIN | dados da pessoa, perfis ativos, histórico de concessões e formulário de concessão | — |
| `/administracao/pessoas/<id>/perfis/conceder/` | POST | ADMIN | perfil, motivo e referência da aprovação obrigatórios; recusa duplicado | `accounts.profile_granted` |
| `/administracao/pessoas/<id>/perfis/<concessao>/revogar/` | POST | ADMIN | motivo obrigatório; recusa o último ADMIN ativo | `accounts.profile_revoked` |
| `/administracao/solicitacoes/` | GET | ADMIN | pendentes e decididas recentemente | — |
| `/administracao/solicitacoes/<id>/decidir/` | POST | ADMIN | `decisao` = `granted` ou `rejected` e motivo obrigatório | `accounts.access_request_decided` |
| `/administracao/bloqueios/` | GET | ADMIN | bloqueios ativos | — |
| `/administracao/bloqueios/<id>/desbloquear/` | POST | ADMIN | motivo obrigatório | `auth.lockout_released` |
| `/auditoria/` | GET | QUALITY, RD_MANAGER, ADMIN | filtros `usuario`, `projeto`, `de`, `ate` (datas locais, inclusivas) e `tipo`; 50 eventos por página, em ordem cronológica | — |
| `/auditoria/exportar/` | GET | QUALITY, RD_MANAGER, ADMIN | mesmos filtros + `formato` = `csv` ou `xlsx`; layout em `exportacao-trilha.md` | `audit.exported` |
| `/auditoria/integridade/` | GET | QUALITY, ADMIN | última verificação, quebras e histórico | — |
| `/auditoria/integridade/verificar/` | POST | QUALITY, ADMIN | enfileira a verificação completa e volta à página com aviso | `audit.chain_verified` (ao terminar) |
| `/saude/` | GET | anônimo | `200 ok` se o banco responde (uso do Docker e do Nginx) | — |

Alerta global: enquanto a verificação mais recente estiver com quebra, toda página mostra a faixa
"Quebra de integridade na trilha de auditoria" para QUALITY e ADMIN, com link para
`/auditoria/integridade/`.

## Comandos de gestão

| Comando | Uso | Eventos |
| --- | --- | --- |
| `grant_initial_admin <login> --motivo --aprovacao` | implantação: só funciona se não houver ADMIN ativo; cria o cadastro mínimo se a pessoa ainda não entrou | `accounts.user_created`, `accounts.profile_granted` |
| `verify_audit_chain` | verificação manual ou por cron; código de saída 1 se houver quebra | `audit.chain_verified` |
| `apply_db_privileges` | reaplica os privilégios do papel da aplicação depois do `migrate` | — |
