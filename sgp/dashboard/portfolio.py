"""Carteira de projetos com consultas agregadas e cache (FR-001, FR-002; research R1 e R2)."""

from collections import Counter
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.db.models import Count
from django.utils import timezone

from sgp.core.formatting import format_decimal_br
from sgp.notebook.models import EntryStatus, NotebookEntry
from sgp.projects.models import Milestone, ProjectStatus
from sgp.projects.permissions import accessible_projects, can_view_financials
from sgp.signatures.models import ApprovedVersion
from sgp.subdocuments.flow import FLOW
from sgp.subdocuments.models import Subdocument, SubdocumentStatus
from sgp.vocab.models import Term

CONCLUDED = "Concluído"


def _labels() -> dict:
    return dict(
        Term.objects.of("tipo-subdocumento").filter(code__in=FLOW).values_list("code", "label")
    )


def _money(value) -> str:
    return f"R$ {format_decimal_br(value, 2)}" if value is not None else "—"


def project_rows(user, today=None) -> list[dict]:
    today = today or timezone.localdate()
    projects = list(
        accessible_projects(user).select_related("leader", "business_plan").order_by("code", "pk")
    )
    ids = [project.pk for project in projects]
    labels = _labels()
    approved_ids = set(
        ApprovedVersion.objects.filter(kind="subdocument", project_id__in=ids).values_list(
            "object_id", flat=True
        )
    )
    approved_types: dict[int, set] = {}
    for sub in Subdocument.objects.filter(
        project_id__in=ids, subdocument_type__code__in=FLOW
    ).values("pk", "project_id", "subdocument_type__code", "status"):
        if sub["status"] == SubdocumentStatus.APPROVED or sub["pk"] in approved_ids:
            approved_types.setdefault(sub["project_id"], set()).add(sub["subdocument_type__code"])
    milestones: dict[int, list] = {}
    for item in (
        Milestone.objects.active()
        .filter(project_id__in=ids)
        .values("project_id", "planned_date", "actual_date")
    ):
        milestones.setdefault(item["project_id"], []).append(item)
    limit = timezone.now() - timedelta(days=int(getattr(settings, "NOTEBOOK_SIGN_DAYS", 7)))
    overdue_entries = dict(
        NotebookEntry.objects.filter(
            project_id__in=ids, status=EntryStatus.OPEN, created_at__lt=limit
        )
        .values("project_id")
        .annotate(total=Count("pk"))
        .values_list("project_id", "total")
    )
    rows = []
    for project in projects:
        done = approved_types.get(project.pk, set())
        stage = next((labels.get(code, code) for code in FLOW if code not in done), CONCLUDED)
        if project.status != ProjectStatus.OPEN:
            stage = project.get_status_display()
        items = milestones.get(project.pk, [])
        late = [
            (today - item["planned_date"]).days
            for item in items
            if item["actual_date"] is None and item["planned_date"] < today
        ]
        financial = can_view_financials(user, project)
        plan = getattr(project, "business_plan", None)
        rows.append(
            {
                "id": project.pk,
                "code": project.code or "",
                "title": project.title,
                "product": project.product_name,
                "leader": project.leader.get_full_name() or project.leader.username,
                "status": project.status,
                "stage": stage,
                "approved": len(done),
                "percent": round(100 * len(done) / len(FLOW)),
                "milestones_planned": len(items),
                "milestones_done": sum(1 for item in items if item["actual_date"]),
                "delay": max(late) if late else (0 if items else None),
                "notebook_overdue": overdue_entries.get(project.pk, 0),
                "financial": financial,
                "cost": _money(plan.total_cost) if financial and plan else "",
                "return": _money(plan.forecast_total) if financial and plan else "",
            }
        )
    return rows


def totals(user, rows) -> dict:
    from sgp.signatures.services import is_approver, review_queue

    queue = review_queue(user) if is_approver(user) else []
    open_rows = [row for row in rows if row["status"] == ProjectStatus.OPEN]
    return {
        "by_stage": sorted(Counter(row["stage"] for row in open_rows).items()),
        "open": len(open_rows),
        "late": sum(1 for row in rows if row["delay"]),
        "waiting": len(queue),
        "longest_wait": max((row["days"] for row in queue), default=0),
        "notebook_overdue": sum(row["notebook_overdue"] for row in rows),
        "approver": is_approver(user),
    }


def cache_key(user) -> str:
    return f"dashboard:portfolio:{user.pk}"


def portfolio(user, *, refresh: bool = False) -> dict:
    """Carteira e totais da pessoa, guardados no cache por `DASHBOARD_CACHE_SECONDS`."""
    key = cache_key(user)
    if not refresh:
        cached = cache.get(key)
        if cached is not None:
            return cached
    rows = project_rows(user)
    data = {"rows": rows, "totals": totals(user, rows), "built_at": timezone.now()}
    cache.set(key, data, int(getattr(settings, "DASHBOARD_CACHE_SECONDS", 300)))
    return data
