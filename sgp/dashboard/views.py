"""Painel, linha do tempo, pendências e exportação (contrato rotas-ui.md da feature 010)."""

from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.http import content_disposition_header
from django.views.decorators.http import require_GET

from sgp.accounts.profiles import deny_access
from sgp.audit.services import record_event
from sgp.core.access import can_access_project
from sgp.projects.models import Project

from . import export, pending, portfolio, timeline

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@require_GET
def portfolio_view(request):
    data = portfolio.portfolio(request.user, refresh=request.GET.get("atualizar") == "1")
    financial = any(row["financial"] for row in data["rows"])
    return render(
        request,
        "dashboard/portfolio.html",
        {"data": data, "financial": financial, "totals": data["totals"]},
    )


@require_GET
def export_view(request):
    data = portfolio.portfolio(request.user, refresh=True)
    content = export.workbook(data["rows"])
    record_event(
        "dashboard.exported",
        actor=request.user,
        object_type="dashboard.portfolio",
        object_id=str(request.user.pk),
        object_repr="Carteira de projetos",
        new_value={
            "projetos": len(data["rows"]),
            "com_dados_financeiros": any(row["financial"] for row in data["rows"]),
        },
        request=request,
    )
    response = HttpResponse(content, content_type=XLSX)
    name = f"carteira-{timezone.localdate().isoformat()}.xlsx"
    response["Content-Disposition"] = content_disposition_header(as_attachment=True, filename=name)
    return response


@require_GET
def timeline_view(request, project_id):
    project = get_object_or_404(Project.objects.select_related("leader"), pk=project_id)
    if not can_access_project(request.user, project):
        return deny_access(request, "sem acesso ao projeto")
    category = request.GET.get("categoria", "")
    queryset = timeline.events(request.user, project, category)
    page = Paginator(queryset, 50).get_page(request.GET.get("pagina"))
    context = {
        "project": project,
        "page": page,
        "rows": timeline.rows(page.object_list),
        "categories": [(code, label) for code, (label, _) in timeline.CATEGORIES.items()],
        "category": category,
        "milestones": timeline.planned_milestones(project),
        "today": timeline.today(),
    }
    return render(request, "dashboard/timeline.html", context)


@require_GET
def pending_view(request):
    return render(request, "dashboard/pending.html", {"data": pending.my_pending(request.user)})
