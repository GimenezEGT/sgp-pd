"""Etapas e assinaturas de modelo somente de inclusão; resumo de base das versões já publicadas.

As versões publicadas antes da feature 013 recebem o resumo do conteúdo na implantação, para que a
verificação de integridade (FR-014) tenha com o que comparar a partir de agora.
"""

from django.db import migrations

from sgp.core.db_triggers import immutable_trigger_sql

TABLES = (
    ("revisions_templatestep", "revisions_templatestep_immutable"),
    ("revisions_templatesignature", "revisions_templatesignature_immutable"),
)
DEFAULT_LOGO_SHA256 = "766852392a3f6104c92d577733ec56fd1d1729bfb39a8da48d72d54fde7a1cea"


def baseline(apps, schema_editor):
    from sgp.signatures.canonical import content_hash

    form_model = apps.get_model("formtemplates", "FormTemplate")
    for template in form_model.objects.filter(status="published", approved_hash=""):
        digest = content_hash(
            {
                "tipo": "form",
                "familia": template.subdocument_type.code,
                "versao": template.form_version,
                "referencia": template.reference,
                "vigencia": template.valid_from,
                "definicao": template.definition,
            }
        )
        form_model.objects.filter(pk=template.pk).update(approved_hash=digest)
    layout_model = apps.get_model("documents", "LayoutTemplate")
    for layout in layout_model.objects.filter(status="published", approved_hash=""):
        logo = layout.logo.sha256 if layout.logo_id else f"padrão {DEFAULT_LOGO_SHA256}"
        digest = content_hash(
            {
                "tipo": "layout",
                "familia": layout.target,
                "versao": layout.version,
                "vigencia": layout.valid_from,
                "logotipo": logo,
                "definicao": layout.definition,
            }
        )
        layout_model.objects.filter(pk=layout.pk).update(approved_hash=digest)


class Migration(migrations.Migration):
    dependencies = [
        ("revisions", "0001_initial"),
        ("core", "0001_forbid_change_function"),
        ("formtemplates", "0004_formtemplate_approved_hash_and_more"),
        ("documents", "0004_layouttemplate_approved_hash_and_more"),
    ]

    operations = [
        *[migrations.RunSQL(*immutable_trigger_sql(table, trigger)) for table, trigger in TABLES],
        migrations.RunPython(baseline, migrations.RunPython.noop),
    ]
