"""Função de trigger compartilhada pelas tabelas somente de inclusão."""

from django.db import migrations

FORBID_FUNCTION = """
CREATE OR REPLACE FUNCTION sgp_forbid_change() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Registro imutável: % em % não é permitido', TG_OP, TG_TABLE_NAME
        USING ERRCODE = 'insufficient_privilege';
END;
$$;
"""


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.RunSQL(FORBID_FUNCTION, reverse_sql="DROP FUNCTION IF EXISTS sgp_forbid_change();"),
    ]
