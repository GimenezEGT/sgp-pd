"""Execuções de qualificação somente de inclusão (gatilho de imutabilidade, feature 014)."""

from django.db import migrations

from sgp.core.db_triggers import immutable_trigger_sql


class Migration(migrations.Migration):
    dependencies = [
        ("operations", "0001_initial"),
        ("core", "0001_forbid_change_function"),
    ]

    operations = [
        migrations.RunSQL(
            *immutable_trigger_sql("operations_qualificationrun", "operations_qualification_immutable")
        ),
    ]
