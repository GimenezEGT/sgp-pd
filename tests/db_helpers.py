"""Ajudantes de banco para os testes: papel da aplicação e simulação de adulteração."""

from django.conf import settings
from django.db import connection, transaction


class _Rollback(Exception):
    pass


def app_role_exists() -> bool:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", [settings.DB_APP_ROLE])
        return cursor.fetchone() is not None


def run_as_app_role(sql: str, params=None) -> None:
    """Executa o SQL com o papel da aplicação num savepoint desfeito ao final.

    Propaga o erro do banco quando o papel não tem o privilégio.
    """
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(f"SET LOCAL ROLE {connection.ops.quote_name(settings.DB_APP_ROLE)}")
                cursor.execute(sql, params or [])
            raise _Rollback
    except _Rollback:
        return


def tamper(
    sql: str, params=None, table: str = "audit_auditevent", trigger: str = "audit_event_immutable"
) -> None:
    """Simula alteração feita direto no banco por quem tem acesso de dono."""
    with connection.cursor() as cursor:
        # As FKs do Django são adiadas; o ALTER TABLE exige que não haja verificações pendentes.
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute(f"ALTER TABLE {table} DISABLE TRIGGER {trigger}")
        cursor.execute(sql, params or [])
        cursor.execute(f"ALTER TABLE {table} ENABLE TRIGGER {trigger}")
        cursor.execute("SET CONSTRAINTS ALL DEFERRED")
