"""Adaptadores dos documentos assinados: subdocumento, TAP e Plano de Negócios (research R1).

Cada adaptador informa o conteúdo canônico (contrato conteudo-canonico.md), a situação, a versão,
a completude, quem edita e o que acontece na aprovação; o serviço de assinatura é um só.
"""

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.urls import reverse

from sgp.files.models import StoredFile

from .models import DocumentKind

DRAFT, IN_REVIEW, RETURNED, APPROVED = "draft", "in_review", "returned", "approved"
EDITABLE = (DRAFT, RETURNED)


class SubdocumentAdapter:
    kind = DocumentKind.SUBDOCUMENT
    label = "Subdocumento"

    def get(self, pk):
        from sgp.subdocuments.models import Subdocument

        return Subdocument.objects.select_related("project", "template", "subdocument_type").get(
            pk=pk
        )

    def lock(self, obj):
        from sgp.subdocuments.models import Subdocument

        return (
            Subdocument.objects.select_for_update()
            .select_related("project", "template", "subdocument_type")
            .get(pk=obj.pk)
        )

    def project(self, obj):
        return obj.project

    def title(self, obj) -> str:
        return str(obj)

    def version(self, obj) -> int:
        return obj.version

    def status(self, obj) -> str:
        return obj.status

    def set_status(self, obj, status: str) -> None:
        obj.status = status
        obj.save(update_fields=["status"])

    def bump_version(self, obj) -> None:
        obj.version += 1
        obj.status = DRAFT
        obj.approved_by = None
        obj.approved_at = None
        obj.row_version += 1
        obj.save(update_fields=["version", "status", "approved_by", "approved_at", "row_version"])

    def attachments(self, obj):
        return list(
            StoredFile.objects.filter(pk__in=(obj.data or {}).get("files", [])).order_by("pk")
        )

    def snapshot(self, obj) -> dict:
        template = obj.template
        content = {
            "documento": "subdocumento",
            "tipo": obj.subdocument_type.code,
            "numero": obj.sequence,
            "versao": obj.version,
            "projeto": obj.project_id,
            "modelo": {
                "id": template.pk,
                "tipo": template.subdocument_type.code,
                "versao": template.form_version,
                "referencia": template.reference,
            },
            "topicos": (obj.data or {}).get("topics", {}),
            "anexos": [
                {"id": item.pk, "nome": item.original_name, "sha256": item.sha256}
                for item in self.attachments(obj)
            ],
        }
        from sgp.studies.services import canonical, linked_studies

        studies = linked_studies(obj)
        if studies:  # feature 007: só quando há estudo, para não mudar resumos já assinados
            content["estudos"] = [canonical(study) for study in studies]
        return content

    def completeness(self, obj) -> list[str]:
        from sgp.subdocuments.services import completeness

        return completeness(obj)

    def can_edit(self, user, obj) -> bool:
        from sgp.subdocuments import permissions

        return obj.status in EDITABLE and permissions.can_edit(user, obj.project)

    def can_create_version(self, user, obj) -> bool:
        from sgp.subdocuments import permissions

        return permissions.can_edit(user, obj.project)

    def on_approved(self, obj, by) -> None:
        from sgp.subdocuments.services import finalize_approval

        finalize_approval(obj, by=by)

    def url(self, obj) -> str:
        return reverse("subdocuments:detail", args=[obj.pk])

    def comparable(self, content: dict) -> dict:
        return content

    def approver_label(self, obj) -> str:
        return obj.template.cover.get("approver_label") or "Gestor de P&D:"


class _ProjectDocumentAdapter:
    """TAP e Plano de Negócios: situação e versão próprias depois do projeto aberto."""

    model_name = ""
    prefix = ""

    def _model(self):
        from sgp.projects import models

        return getattr(models, self.model_name)

    def get(self, pk):
        return self._model().objects.select_related("project").get(pk=pk)

    def lock(self, obj):
        return self._model().objects.select_for_update().select_related("project").get(pk=obj.pk)

    def project(self, obj):
        return obj.project

    def version(self, obj) -> int:
        return obj.doc_version

    def status(self, obj) -> str:
        return obj.doc_status

    def set_status(self, obj, status: str) -> None:
        obj.doc_status = status
        obj.save(update_fields=["doc_status"])

    def bump_version(self, obj) -> None:
        obj.doc_version += 1
        obj.doc_status = DRAFT
        obj.save(update_fields=["doc_version", "doc_status"])

    def attachments(self, obj):
        return []

    def completeness(self, obj) -> list[str]:
        from sgp.projects.completeness import pending_items

        return [item for item in pending_items(obj.project) if item.startswith(self.prefix)]

    def can_edit(self, user, obj) -> bool:
        from sgp.projects.models import ProjectStatus
        from sgp.projects.permissions import is_leader

        project = obj.project
        if not is_leader(user, project):
            return False
        if project.status == ProjectStatus.OPEN:
            return obj.doc_status in EDITABLE
        return project.is_editable

    def can_create_version(self, user, obj) -> bool:
        from sgp.projects.models import ProjectStatus
        from sgp.projects.permissions import is_leader

        return is_leader(user, obj.project) and obj.project.status == ProjectStatus.OPEN

    def on_approved(self, obj, by) -> None:
        return None

    def url(self, obj) -> str:
        return reverse("projects:detail", args=[obj.project_id])

    def comparable(self, content: dict) -> dict:
        """Equipe e marcos mudam na execução do projeto; o TAP aprovado não muda."""
        return {key: value for key, value in content.items() if key not in ("equipe", "marcos")}

    def approver_label(self, obj) -> str:
        return "Gestor de P&D:"


class CharterAdapter(_ProjectDocumentAdapter):
    kind = DocumentKind.CHARTER
    label = "TAP"
    model_name = "ProjectCharter"
    prefix = ("TAP:", "Produto:")

    def title(self, obj) -> str:
        return f"TAP – {obj.project.title} – versão {obj.doc_version:02d}"

    def completeness(self, obj) -> list[str]:
        from sgp.projects.completeness import pending_items

        return [item for item in pending_items(obj.project) if item.startswith(self.prefix)]

    def snapshot(self, obj) -> dict:
        from sgp.projects.services import CHARTER_FIELDS, _product_snapshot

        project = obj.project
        members = project.members.select_related("user").order_by("start_date", "pk")
        milestones = project.milestones.select_related("subdocument_type").order_by(
            "planned_date", "pk"
        )
        return {
            "documento": "tap",
            "versao": obj.doc_version,
            "projeto": project.pk,
            "produto": _product_snapshot(project),
            "tap": {field: getattr(obj, field) for field in CHARTER_FIELDS},
            "equipe": [
                {
                    "pessoa": member.user.username,
                    "papel": member.role,
                    "inicio": member.start_date,
                    "fim": member.end_date,
                }
                for member in members
            ],
            "marcos": [
                {
                    "subdocumento": milestone.subdocument_type.code,
                    "descricao": milestone.description,
                    "planejado": milestone.planned_date,
                    "realizado": milestone.actual_date,
                    "cancelado": milestone.canceled_at is not None,
                }
                for milestone in milestones
            ],
        }


class BusinessPlanAdapter(_ProjectDocumentAdapter):
    kind = DocumentKind.BUSINESS_PLAN
    label = "Plano de Negócios"
    model_name = "BusinessPlan"
    prefix = "Plano de Negócios:"

    def title(self, obj) -> str:
        return f"Plano de Negócios – {obj.project.title} – versão {obj.doc_version:02d}"

    def snapshot(self, obj) -> dict:
        from sgp.projects.services import PLAN_FIELDS

        return {
            "documento": "plano_de_negocios",
            "versao": obj.doc_version,
            "projeto": obj.project_id,
            "plano": {field: getattr(obj, field) for field in PLAN_FIELDS},
            "previsoes": {
                str(f.year_index): f.amount for f in obj.forecasts.order_by("year_index")
            },
            "total": obj.forecast_total,
        }


ADAPTERS = {
    adapter.kind: adapter
    for adapter in (SubdocumentAdapter(), CharterAdapter(), BusinessPlanAdapter())
}


def get_adapter(kind: str):
    try:
        return ADAPTERS[kind]
    except KeyError:
        raise Http404("Tipo de documento inexistente.") from None


def load(kind: str, pk):
    adapter = get_adapter(kind)
    try:
        return adapter, adapter.get(pk)
    except ObjectDoesNotExist:
        raise Http404("Documento inexistente.") from None
