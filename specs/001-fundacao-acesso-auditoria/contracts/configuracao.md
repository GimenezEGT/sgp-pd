# Contrato: variáveis de ambiente (feature 001)

Nenhum segredo fica no repositório; `.env.example` lista as variáveis com valores fictícios.

| Variável | Padrão | Uso |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | — (obrigatória) | chave de assinatura de sessões e CSRF |
| `DJANGO_DEBUG` | `false` | só `true` em desenvolvimento |
| `DJANGO_ALLOWED_HOSTS` | `localhost` | nomes do servidor, separados por vírgula |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://localhost` | origens HTTPS confiáveis |
| `DB_HOST` / `DB_PORT` / `DB_NAME` | `db` / `5432` / `sgp` | banco |
| `DB_USER` / `DB_PASSWORD` | `sgp_app` / — | papel da aplicação em execução |
| `DB_OWNER_USER` / `DB_OWNER_PASSWORD` | `sgp_owner` / — | migrações, privilégios e testes |
| `REDIS_URL` | `redis://redis:6379/0` | fila do Celery |
| `SESSION_IDLE_TIMEOUT_MINUTES` | `30` | inatividade (FR-005) |
| `LOGIN_MAX_FAILURES` | `5` | tentativas inválidas seguidas (FR-006) |
| `LOGIN_LOCKOUT_MINUTES` | `15` | duração do bloqueio (FR-006) |
| `AUDIT_VERIFY_HOUR` / `AUDIT_VERIFY_MINUTE` | `2` / `0` | horário da verificação diária (America/Sao_Paulo) |
| `ACCESS_REQUEST_INSTRUCTIONS` | texto padrão | instruções da página "Solicitar acesso" |
| `LDAP_SERVER_URI` | — | ex.: `ldaps://ad.empresa.local` |
| `LDAP_START_TLS` | `false` | StartTLS sobre `ldap://` |
| `LDAP_CA_CERT_FILE` | vazio | CA da empresa para validar o servidor |
| `LDAP_BIND_DN` / `LDAP_BIND_PASSWORD` | — | conta de serviço de consulta |
| `LDAP_USER_SEARCH_BASE` | — | base de busca de usuários |
| `LDAP_USER_FILTER` | `(sAMAccountName=%(user)s)` | filtro de usuário |
| `LDAP_GROUP_SEARCH_BASE` | vazio | base de grupos (necessária para o mapeamento) |
| `LDAP_GROUP_FILTER` | `(objectClass=group)` | filtro de grupos |
| `LDAP_GROUP_TYPE` | `active_directory_nested` | ou `group_of_names` (desenvolvimento) |
| `LDAP_ATTR_FIRST_NAME`, `LDAP_ATTR_LAST_NAME`, `LDAP_ATTR_FULL_NAME`, `LDAP_ATTR_EMAIL`, `LDAP_ATTR_JOB_TITLE` | `givenName`, `sn`, `displayName`, `mail`, `title` | mapa de atributos |
| `LDAP_PROFILE_GROUPS` | vazio | JSON perfil → DN do grupo, ex.: `{"ANALYST": "CN=SGP-Analistas,OU=Grupos,DC=empresa,DC=local"}` |
| `LDAP_TIMEOUT_SECONDS` | `5` | tempo máximo de rede do LDAP |
| `LOG_LEVEL` | `INFO` | nível de log |
| `LDAP_LOG_LEVEL` | `WARNING` | nível de log do django-auth-ldap (nunca registra senha) |
| `DB_APP_ROLE` | `sgp_app` | papel que recebe os privilégios do `apply_db_privileges` |
| `DB_CONN_MAX_AGE` | `60` | reaproveitamento de conexões do banco, em segundos |
| `DJANGO_SECURE_COOKIES` | `true` | cookies de sessão e CSRF só por HTTPS |
| `SGP_CLIENT_IP_HEADER` | `HTTP_X_REAL_IP` | cabeçalho com o IP de origem enviado pelo Nginx |
| `HTTPS_PORT` / `HTTP_PORT` | `443` / `80` | portas publicadas pelo Nginx (desenvolvimento: `8443` / `8080`) |
| `SGP_CERT_CN` | `localhost` | nome do certificado autoassinado gerado só quando nenhum certificado é montado |
| `GUNICORN_WORKERS` / `GUNICORN_TIMEOUT` | `3` / `120` | processos e tempo limite do gunicorn |
| `CELERY_CONCURRENCY` / `CELERY_LOG_LEVEL` | `2` / `INFO` | worker do Celery |
| `LDAP_DEV_ADMIN_PASSWORD` | fictícia | só no `docker-compose.override.yml` (LDAP de desenvolvimento) |
