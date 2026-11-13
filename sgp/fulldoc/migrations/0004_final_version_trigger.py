"""Versões do documento final somente de inclusão (gatilho de imutabilidade, feature 016)."""

from django.db import migrations

from sgp.core.db_triggers import immutable_trigger_sql


class Migration(migrations.Migration):
    dependencies = [
        ("fulldoc", "0003_final_document_version"),
        ("core", "0001_forbid_change_function"),
    ]

    operations = [
        migrations.RunSQL(
            *immutable_trigger_sql("fulldoc_finaldocumentversion", "fulldoc_final_version_immutable")
        ),
    ]
