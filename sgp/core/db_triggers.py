"""SQL dos triggers que impedem UPDATE e DELETE em tabelas somente de inclusão."""


def immutable_trigger_sql(table: str, trigger: str) -> tuple[str, str]:
    forward = (
        f"CREATE TRIGGER {trigger} BEFORE UPDATE OR DELETE ON {table} "
        "FOR EACH ROW EXECUTE FUNCTION sgp_forbid_change();"
    )
    reverse = f"DROP TRIGGER IF EXISTS {trigger} ON {table};"
    return forward, reverse
