"""Documento completo arquivado é somente de inclusão (data-model.md da feature 009)."""

from django.db import migrations

from sgp.core.db_triggers import immutable_trigger_sql


class Migration(migrations.Migration):
    dependencies = [
        ("fulldoc", "0001_initial"),
        ("core", "0001_forbid_change_function"),
    ]

    operations = [
        migrations.RunSQL(*immutable_trigger_sql("fulldoc_fulldocument", "fulldoc_document_immutable")),
    ]
