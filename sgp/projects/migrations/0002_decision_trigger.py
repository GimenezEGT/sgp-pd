"""Decisões do projeto são somente de inclusão: trigger contra UPDATE e DELETE."""

from django.db import migrations

from sgp.core.db_triggers import immutable_trigger_sql

FORWARD, REVERSE = immutable_trigger_sql("projects_projectdecision", "projects_decision_immutable")


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0001_initial"),
        ("core", "0001_forbid_change_function"),
    ]

    operations = [migrations.RunSQL(FORWARD, reverse_sql=REVERSE)]
