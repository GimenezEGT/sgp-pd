"""TAP e Plano de projetos já existentes recebem a situação de documento do projeto (feature 005)."""

from django.db import migrations

MAP = {"draft": "draft", "submitted": "in_review", "returned": "returned", "open": "approved"}


def forwards(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    ProjectCharter = apps.get_model("projects", "ProjectCharter")
    BusinessPlan = apps.get_model("projects", "BusinessPlan")
    for project in Project.objects.all():
        status = MAP.get(project.status, "draft")
        ProjectCharter.objects.filter(project=project).update(doc_status=status)
        BusinessPlan.objects.filter(project=project).update(doc_status=status)


class Migration(migrations.Migration):
    dependencies = [("projects", "0003_businessplan_doc_status_businessplan_doc_version_and_more")]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
