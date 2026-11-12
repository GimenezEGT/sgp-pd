"""Lista controlada dos tipos de estudo (feature 007)."""

from django.db import migrations

from sgp.vocab.seed import STUDY_SEED, load


def forwards(apps, schema_editor):
    load(apps, STUDY_SEED)


class Migration(migrations.Migration):
    dependencies = [("vocab", "0004_seed_subdocumentos")]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
