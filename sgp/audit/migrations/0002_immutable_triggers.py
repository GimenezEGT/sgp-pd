"""Triggers que recusam UPDATE e DELETE na trilha e nas verificações (FR-019, FR-021)."""

from django.db import migrations

from sgp.core.db_triggers import immutable_trigger_sql

EVENT_FORWARD, EVENT_REVERSE = immutable_trigger_sql("audit_auditevent", "audit_event_immutable")
CHECK_FORWARD, CHECK_REVERSE = immutable_trigger_sql(
    "audit_chainverification", "audit_verification_immutable"
)


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0001_initial"),
        ("core", "0001_forbid_change_function"),
    ]

    operations = [
        migrations.RunSQL(EVENT_FORWARD, reverse_sql=EVENT_REVERSE),
        migrations.RunSQL(CHECK_FORWARD, reverse_sql=CHECK_REVERSE),
    ]
