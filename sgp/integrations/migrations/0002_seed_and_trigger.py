"""Mapeamento padrão (versão 1, entidades vazias) e imutabilidade das versões do mapeamento."""

from django.db import migrations

from sgp.core.db_triggers import immutable_trigger_sql


def seed(apps, schema_editor):
    from sgp.integrations import mapping

    model = apps.get_model("integrations", "IntegrationMapping")
    if model.objects.exists():
        return
    text = mapping.default_yaml()
    model.objects.create(
        version=1,
        yaml=text,
        parsed=mapping.parse(text),
        note="Registros do contexto; entidades a definir com a consultoria Sankhya.",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("integrations", "0001_initial"),
        ("core", "0001_forbid_change_function"),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
        migrations.RunSQL(
            *immutable_trigger_sql("integrations_integrationmapping", "integrations_mapping_immutable")
        ),
    ]
