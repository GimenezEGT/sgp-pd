"""Carga inicial: modelos versão 05 dos nove subdocumentos (FR-006 da feature 004)."""

from django.db import migrations
from django.utils import timezone

from sgp.formtemplates.seed_v05 import load


def forwards(apps, schema_editor):
    load(apps, valid_from=timezone.localdate(), published_at=timezone.now())


class Migration(migrations.Migration):
    dependencies = [
        ("formtemplates", "0002_published_immutable"),
        ("vocab", "0004_seed_subdocumentos"),
    ]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
