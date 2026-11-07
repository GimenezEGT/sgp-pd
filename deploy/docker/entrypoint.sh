#!/bin/sh
# Ponto de entrada da imagem do SGP-P&D.
#   web      migrações (papel dono) + privilégios + gunicorn (papel da aplicação)
#   web-dev  migrações + privilégios + runserver (desenvolvimento)
#   worker   Celery com o agendador embutido (verificação diária da trilha)
#   outro    executa o comando informado (ex.: pytest, python manage.py ...)
set -eu

wait_for_db() {
    python - <<'PY'
import os, sys, time
import psycopg

params = dict(
    host=os.environ.get("DB_HOST", "db"),
    port=os.environ.get("DB_PORT", "5432"),
    dbname=os.environ.get("DB_NAME", "sgp"),
    user=os.environ.get("DB_OWNER_USER", "sgp_owner"),
    password=os.environ.get("DB_OWNER_PASSWORD", ""),
    connect_timeout=3,
)
for attempt in range(60):
    try:
        psycopg.connect(**params).close()
        sys.exit(0)
    except psycopg.OperationalError:
        time.sleep(2)
print("Banco de dados indisponível.", file=sys.stderr)
sys.exit(1)
PY
}

as_owner() {
    DB_USER="${DB_OWNER_USER:-sgp_owner}" DB_PASSWORD="${DB_OWNER_PASSWORD:-}" "$@"
}

prepare_database() {
    wait_for_db
    as_owner python manage.py migrate --noinput
    as_owner python manage.py apply_db_privileges
}

case "${1:-web}" in
    web)
        prepare_database
        exec gunicorn config.wsgi:application \
            --bind 0.0.0.0:8000 \
            --workers "${GUNICORN_WORKERS:-3}" \
            --timeout "${GUNICORN_TIMEOUT:-120}" \
            --access-logfile - \
            --forwarded-allow-ips "*"
        ;;
    web-dev)
        prepare_database
        exec python manage.py runserver 0.0.0.0:8000
        ;;
    worker)
        wait_for_db
        exec celery -A config worker --beat --loglevel "${CELERY_LOG_LEVEL:-INFO}" \
            --schedule /tmp/celerybeat-schedule --concurrency "${CELERY_CONCURRENCY:-2}"
        ;;
    *)
        exec "$@"
        ;;
esac
