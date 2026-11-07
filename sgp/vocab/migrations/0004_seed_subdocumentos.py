"""Listas do formulário de entrada, da Verificação Final e da Saída (feature 004)."""

from django.db import migrations

from sgp.vocab.seed import SUBDOCUMENT_SEED, load


def forwards(apps, schema_editor):
    load(apps, SUBDOCUMENT_SEED)


class Migration(migrations.Migration):
    dependencies = [("vocab", "0003_seed_amostras")]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
