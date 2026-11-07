"""Versões aprovadas, assinaturas, tentativas e comentários são somente de inclusão (FR-010)."""

from django.db import migrations

from sgp.core.db_triggers import immutable_trigger_sql

TABLES = (
    ("signatures_approvedversion", "signatures_approvedversion_immutable"),
    ("signatures_signature", "signatures_signature_immutable"),
    ("signatures_signatureattempt", "signatures_attempt_immutable"),
    ("signatures_reviewcomment", "signatures_comment_immutable"),
)


class Migration(migrations.Migration):
    dependencies = [
        ("signatures", "0001_initial"),
        ("core", "0001_forbid_change_function"),
    ]

    operations = [
        migrations.RunSQL(*immutable_trigger_sql(table, trigger)) for table, trigger in TABLES
    ]
