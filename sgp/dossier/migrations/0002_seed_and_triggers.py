"""Definição padrão do dossiê (versão 1) e imutabilidade das definições e versões."""

from django.db import migrations

from sgp.core.db_triggers import immutable_trigger_sql


def seed(apps, schema_editor):
    from sgp.dossier import definition

    model = apps.get_model("dossier", "DossierDefinition")
    if model.objects.exists():
        return
    text = definition.default_yaml()
    model.objects.create(
        version=1,
        yaml=text,
        parsed=definition.parse(text),
        note="Estrutura I a XII do contexto (docs/contexto/03-padroes-formatacao.md).",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("dossier", "0001_initial"),
        ("core", "0001_forbid_change_function"),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
        migrations.RunSQL(*immutable_trigger_sql("dossier_dossierdefinition", "dossier_definition_immutable")),
        migrations.RunSQL(*immutable_trigger_sql("dossier_dossierversion", "dossier_version_immutable")),
    ]
