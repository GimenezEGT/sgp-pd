"""Metadados de arquivo são somente de inclusão: trigger contra UPDATE e DELETE."""

from django.db import migrations

from sgp.core.db_triggers import immutable_trigger_sql

FORWARD, REVERSE = immutable_trigger_sql("files_storedfile", "files_storedfile_immutable")


class Migration(migrations.Migration):
    dependencies = [
        ("files", "0001_initial"),
        ("core", "0001_forbid_change_function"),
    ]

    operations = [migrations.RunSQL(FORWARD, reverse_sql=REVERSE)]
