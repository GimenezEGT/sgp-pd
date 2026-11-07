"""Carga inicial das listas de tecnologia e de tipos de subdocumento (feature 002)."""

from django.db import migrations

from sgp.vocab.seed import SEED, load


def forwards(apps, schema_editor):
    load(apps, SEED)


class Migration(migrations.Migration):
    dependencies = [("vocab", "0001_initial")]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
