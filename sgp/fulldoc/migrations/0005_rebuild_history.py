"""Reconstrução das versões do documento final a partir das aprovações já registradas
(FR-009 da feature 016). A reversão não apaga nada (registros somente de inclusão)."""

from django.db import migrations


def forward(apps, schema_editor):
    from sgp.fulldoc.history import rebuild

    rebuild(apps)


class Migration(migrations.Migration):
    dependencies = [
        ("fulldoc", "0004_final_version_trigger"),
        ("signatures", "0003_approvedversion_signatures_approved_proj_idx"),
        ("subdocuments", "0003_alter_subdocument_status"),
        ("projects", "0005_milestone_projects_milestone_plan_idx"),
        ("vocab", "0005_seed_estudos"),
    ]

    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
