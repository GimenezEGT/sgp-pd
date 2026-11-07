#!/bin/bash
# Cria o papel de banco da aplicação (sem privilégios de tabela: o comando
# apply_db_privileges concede SELECT/INSERT/UPDATE depois de cada migração).
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
    -v app_user="${APP_DB_USER:-sgp_app}" -v app_password="${APP_DB_PASSWORD:?defina APP_DB_PASSWORD}" <<'EOSQL'
SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'app_user', :'app_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'app_user')
\gexec
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO :"app_user";
EOSQL
