"""Autorizações de fluxo e seus usos são somente de inclusão: gatilhos contra UPDATE e DELETE."""

from django.db import migrations

from sgp.core.db_triggers import immutable_trigger_sql

AUTH_FORWARD, AUTH_REVERSE = immutable_trigger_sql(
    "subdocuments_flowauthorization", "subdocuments_authorization_immutable"
)
USE_FORWARD, USE_REVERSE = immutable_trigger_sql(
    "subdocuments_flowauthorizationuse", "subdocuments_authorization_use_immutable"
)


class Migration(migrations.Migration):
    dependencies = [
        ("subdocuments", "0001_initial"),
        ("core", "0001_forbid_change_function"),
    ]

    operations = [
        migrations.RunSQL(AUTH_FORWARD, reverse_sql=AUTH_REVERSE),
        migrations.RunSQL(USE_FORWARD, reverse_sql=USE_REVERSE),
    ]
