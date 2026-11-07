"""Privilégios do papel de banco da aplicação.

O papel da aplicação recebe SELECT, INSERT e UPDATE em todas as tabelas e DELETE só nas tabelas
técnicas listadas em DELETABLE_TABLES. As tabelas de modelos AppendOnlyModel perdem o UPDATE.
TRUNCATE nunca é concedido. Executado pelo papel dono depois de cada migração.
"""

from django.apps import apps
from django.db import connection

DELETABLE_TABLES = ("django_session",)


def append_only_tables() -> list[str]:
    return sorted(
        model._meta.db_table
        for model in apps.get_models()
        if getattr(model, "append_only", False) and not model._meta.proxy
    )


def role_exists(role: str) -> bool:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", [role])
        return cursor.fetchone() is not None


def apply_privileges(role: str) -> dict:
    quote = connection.ops.quote_name
    target = quote(role)
    existing = set(connection.introspection.table_names())
    deletable = [table for table in DELETABLE_TABLES if table in existing]
    append_only = [table for table in append_only_tables() if table in existing]
    with connection.cursor() as cursor:
        cursor.execute(f"GRANT USAGE ON SCHEMA public TO {target}")
        cursor.execute(f"REVOKE ALL ON ALL TABLES IN SCHEMA public FROM {target}")
        cursor.execute(f"GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO {target}")
        cursor.execute(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {target}")
        for table in deletable:
            cursor.execute(f"GRANT DELETE ON {quote(table)} TO {target}")
        for table in append_only:
            cursor.execute(f"REVOKE UPDATE ON {quote(table)} FROM {target}")
    return {"deletable": deletable, "append_only": append_only}
