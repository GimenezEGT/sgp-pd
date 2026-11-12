"""Versão 01 publicada dos layouts de subdocumentos, TAP e Plano de Negócios (vigência 2020-01-01)."""

import datetime

from django.db import migrations
from django.utils import timezone


def forward(apps, schema_editor):
    from sgp.documents import seed

    seed.load(apps, valid_from=datetime.date(2020, 1, 1), published_at=timezone.now())


class Migration(migrations.Migration):
    dependencies = [("documents", "0002_triggers")]

    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
