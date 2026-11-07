"""Trigger que recusa UPDATE e DELETE nas tentativas de login (somente inclusão)."""

from django.db import migrations

from sgp.core.db_triggers import immutable_trigger_sql

FORWARD, REVERSE = immutable_trigger_sql("accounts_loginattempt", "accounts_loginattempt_immutable")


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("core", "0001_forbid_change_function"),
    ]

    operations = [migrations.RunSQL(FORWARD, reverse_sql=REVERSE)]
