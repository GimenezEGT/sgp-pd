"""Carga inicial das listas de tipos de amostra e de armazenamento (feature 003)."""

from django.db import migrations

from sgp.vocab.seed import SAMPLE_SEED, load


def forwards(apps, schema_editor):
    load(apps, SAMPLE_SEED)


class Migration(migrations.Migration):
    dependencies = [("vocab", "0002_seed")]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
