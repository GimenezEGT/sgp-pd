"""Linha do tempo do projeto a partir da trilha (FR-003; research R6)."""

from django.db.models import Q
from django.utils import timezone

from sgp.audit.event_types import label_for
from sgp.audit.models import AuditEvent
from sgp.projects.models import Milestone
from sgp.projects.permissions import can_view_financials

CATEGORIES = {
    "marcos": ("Marcos", ("projects.milestone_",)),
    "documentos": (
        "Subdocumentos e versões",
        (
            "subdocuments.",
            "signatures.new_version",
            "documents.generated",
            "fulldoc.generated",
            "fulldoc.version_created",
        ),
    ),
    "assinaturas": (
        "Assinaturas e decisões",
        ("signatures.", "projects.submitted", "projects.returned", "projects.approved"),
    ),
    "alteracoes": ("Alterações de projeto", ("projects.version_changed",)),
    "caderno": ("Caderno de laboratório", ("notebook.",)),
    "estudos": ("Estudos", ("studies.",)),
}
CHANGE_LABEL = "Alteração de Projeto"


def _category_filter(code: str) -> Q:
    _, prefixes = CATEGORIES[code]
    query = Q()
    for prefix in prefixes:
        query |= Q(event_type__startswith=prefix)
    if code == "alteracoes":
        query |= Q(object_repr__icontains=CHANGE_LABEL)
    return query


def events(user, project, category: str = ""):
    queryset = AuditEvent.objects.filter(project_id=project.pk)
    if category in CATEGORIES:
        queryset = queryset.filter(_category_filter(category))
    else:
        every = Q()
        for code in CATEGORIES:
            every |= _category_filter(code)
        queryset = queryset.filter(every)
    if not can_view_financials(user, project):
        queryset = queryset.exclude(object_type="projects.businessplan").exclude(
            event_type="projects.business_plan_updated"
        )
    return queryset.order_by("-seq")


def rows(page) -> list[dict]:
    return [
        {
            "at": event.occurred_at,
            "who": event.actor_username,
            "event": label_for(event.event_type),
            "record": event.object_repr,
            "reason": event.reason,
        }
        for event in page
    ]


def planned_milestones(project) -> list:
    """Marcos ativos ainda não realizados, do mais próximo para o mais distante."""
    return list(
        Milestone.objects.active()
        .filter(project=project, actual_date__isnull=True)
        .select_related("subdocument_type")
        .order_by("planned_date")
    )


def today():
    return timezone.localdate()
