"""Telas de projetos: lista, criação, detalhe, TAP, Plano de Negócios, equipe, marcos e decisões."""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from sgp.accounts.profiles import (
    Profile,
    active_profiles,
    deny_access,
    profile_required,
)

from . import services, workflow
from .completeness import pending_items
from .forms import (
    BusinessPlanForm,
    CharterForm,
    EndMemberForm,
    MemberForm,
    MilestoneForm,
    MilestoneUpdateForm,
    ProductForm,
    ProjectFilterForm,
    ReasonForm,
    ReturnForm,
    RiskFormSet,
    StakeholderFormSet,
    rows_from_formset,
)
from .models import Milestone, ProjectMember, ProjectStatus
from .permissions import (
    CREATE_PROFILES,
    accessible_projects,
    can_decide,
    can_edit_documents,
    can_manage_team,
    can_view_financials,
    get_project_or_deny,
    is_leader,
)


def _errors(request, exc: ValidationError) -> None:
    for message in exc.messages:
        messages.error(request, message)


@require_GET
def project_list(request):
    form = ProjectFilterForm(request.GET or None)
    projects = accessible_projects(request.user)
    if form.is_valid():
        data = form.cleaned_data
        if data.get("status"):
            projects = projects.filter(status=data["status"])
        if data.get("lider"):
            projects = projects.filter(leader=data["lider"])
        if data.get("produto"):
            term = data["produto"]
            projects = projects.filter(
                Q(product_name__icontains=term) | Q(product_family__icontains=term)
            )
    rows = [(project, can_view_financials(request.user, project)) for project in projects[:500]]
    context = {
        "form": form,
        "rows": rows,
        "show_cost": any(can for _, can in rows),
        "can_create": bool(active_profiles(request.user) & CREATE_PROFILES),
    }
    return render(request, "projects/list.html", context)


@require_http_methods(["GET", "POST"])
@profile_required(*CREATE_PROFILES)
def project_new(request):
    with_leader = Profile.PROJECT_LEADER not in active_profiles(request.user)
    form = ProductForm(request.POST or None, with_leader=with_leader)
    if request.method == "POST" and form.is_valid():
        try:
            project = services.create_project(
                by=request.user, data=form.product_data(), leader=form.cleaned_data.get("leader")
            )
        except ValidationError as exc:
            _errors(request, exc)
        else:
            messages.success(request, "Projeto criado em rascunho.")
            return redirect("projects:detail", project_id=project.pk)
    return render(request, "projects/product_form.html", {"form": form, "project": None})


@require_GET
def project_detail(request, project_id):
    project, denied = get_project_or_deny(request, project_id)
    if denied:
        return denied
    user = request.user
    plan = project.business_plan
    leader = is_leader(user, project)
    context = {
        "project": project,
        "charter": project.charter,
        "plan": plan,
        "forecasts": list(plan.forecasts.order_by("year_index")),
        "forecast_total": plan.forecast_total,
        "members": project.members.select_related("user").order_by("end_date", "start_date"),
        "milestones": project.milestones.select_related("subdocument_type"),
        "decisions": project.decisions.select_related("actor"),
        "can_view_financials": can_view_financials(user, project),
        "is_leader": leader,
        "can_edit": can_edit_documents(user, project),
        "can_manage_team": can_manage_team(user, project),
        "can_decide": can_decide(user, project) and project.status == ProjectStatus.SUBMITTED,
        "pending": pending_items(project) if leader and project.is_editable else [],
        "member_form": MemberForm(),
        "end_member_form": EndMemberForm(),
        "milestone_form": MilestoneForm(),
        "milestone_update_form": MilestoneUpdateForm(),
        "reason_form": ReasonForm(),
        "return_form": ReturnForm(),
    }
    return render(request, "projects/detail.html", context)


def _leader_only(request, project, *, documents: bool):
    if not is_leader(request.user, project):
        return deny_access(request, "só o líder do projeto")
    if documents and not project.is_editable:
        messages.error(
            request, "O projeto não está em rascunho nem devolvido; a edição está bloqueada."
        )
        return redirect("projects:detail", project_id=project.pk)
    return None


@require_http_methods(["GET", "POST"])
def project_edit(request, project_id):
    project, denied = get_project_or_deny(request, project_id)
    if denied:
        return denied
    blocked = _leader_only(request, project, documents=True)
    if blocked:
        return blocked
    initial = {
        "title": project.title,
        "product_name": project.product_name,
        "product_family": project.product_family,
        "technology": project.technology_id,
        "regulatory_body": project.regulatory_body,
        "risk_class": project.risk_class,
        "classification_rule": project.classification_rule,
        "row_version": project.row_version,
    }
    form = ProductForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            services.update_product(
                project,
                by=request.user,
                data=form.product_data(),
                row_version=form.cleaned_data["row_version"],
            )
        except ValidationError as exc:
            _errors(request, exc)
        else:
            messages.success(request, "Dados do produto salvos.")
            return redirect("projects:detail", project_id=project.pk)
    return render(request, "projects/product_form.html", {"form": form, "project": project})


@require_http_methods(["GET", "POST"])
def charter_edit(request, project_id):
    project, denied = get_project_or_deny(request, project_id)
    if denied:
        return denied
    blocked = _leader_only(request, project, documents=True)
    if blocked:
        return blocked
    charter = project.charter
    initial = {field: getattr(charter, field) for field in services.CHARTER_FIELDS}
    initial["row_version"] = charter.row_version
    if request.method == "POST":
        form = CharterForm(request.POST)
        risks = RiskFormSet(request.POST, prefix="riscos")
        stakeholders = StakeholderFormSet(request.POST, prefix="partes")
        if form.is_valid() and risks.is_valid() and stakeholders.is_valid():
            data = {
                key: form.cleaned_data[key]
                for key in services.CHARTER_FIELDS
                if key in form.cleaned_data
            }
            data["risks"] = rows_from_formset(risks, ("risco", "impacto", "resposta"))
            data["stakeholders"] = rows_from_formset(stakeholders, ("nome_area", "interesse"))
            try:
                services.update_charter(
                    project,
                    by=request.user,
                    data=data,
                    row_version=form.cleaned_data["row_version"],
                )
            except ValidationError as exc:
                _errors(request, exc)
            else:
                messages.success(request, "TAP salvo.")
                return redirect("projects:detail", project_id=project.pk)
    else:
        form = CharterForm(initial=initial)
        risks = RiskFormSet(initial=charter.risks, prefix="riscos")
        stakeholders = StakeholderFormSet(initial=charter.stakeholders, prefix="partes")
    context = {"form": form, "risks": risks, "stakeholders": stakeholders, "project": project}
    return render(request, "projects/charter_form.html", context)


@require_http_methods(["GET", "POST"])
def business_plan_edit(request, project_id):
    project, denied = get_project_or_deny(request, project_id)
    if denied:
        return denied
    blocked = _leader_only(request, project, documents=True)
    if blocked:
        return blocked
    plan = project.business_plan
    initial = {key: getattr(plan, key) for key in BusinessPlanForm.PLAN_KEYS}
    initial.update({f"forecast_{f.year_index}": f.amount for f in plan.forecasts.all()})
    initial["row_version"] = plan.row_version
    form = BusinessPlanForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            services.update_business_plan(
                project,
                by=request.user,
                data=form.plan_data(),
                forecasts=form.forecasts(),
                row_version=form.cleaned_data["row_version"],
            )
        except ValidationError as exc:
            _errors(request, exc)
        else:
            messages.success(request, "Plano de Negócios salvo.")
            return redirect("projects:detail", project_id=project.pk)
    return render(request, "projects/business_plan_form.html", {"form": form, "project": project})


def _post_action(request, project_id, handler):
    project, denied = get_project_or_deny(request, project_id)
    if denied:
        return denied
    if not is_leader(request.user, project):
        return deny_access(request, "só o líder do projeto")
    try:
        message = handler(project)
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(request, message)
    return redirect("projects:detail", project_id=project.pk)


@require_POST
def member_add(request, project_id):
    def handler(project):
        form = MemberForm(request.POST)
        if not form.is_valid():
            raise ValidationError("Escolha a pessoa e informe o papel no projeto.")
        services.add_member(
            project,
            by=request.user,
            user=form.cleaned_data["user"],
            role=form.cleaned_data["role"],
            start_date=form.cleaned_data.get("start_date"),
        )
        return "Membro incluído na equipe."

    return _post_action(request, project_id, handler)


@require_POST
def member_end(request, project_id, member_id):
    def handler(project):
        member = get_object_or_404(ProjectMember, pk=member_id, project=project)
        form = EndMemberForm(request.POST)
        if not form.is_valid():
            raise ValidationError("Informe o motivo do encerramento.")
        services.end_member(
            member,
            by=request.user,
            reason=form.cleaned_data["reason"],
            end_date=form.cleaned_data.get("end_date"),
        )
        return "Vigência encerrada."

    return _post_action(request, project_id, handler)


@require_POST
def milestone_add(request, project_id):
    def handler(project):
        form = MilestoneForm(request.POST)
        if not form.is_valid():
            raise ValidationError("Escolha o subdocumento e informe a data planejada.")
        services.add_milestone(
            project,
            by=request.user,
            subdocument_type=form.cleaned_data["subdocument_type"],
            planned_date=form.cleaned_data["planned_date"],
            description=form.cleaned_data.get("description", ""),
        )
        return "Marco incluído."

    return _post_action(request, project_id, handler)


@require_POST
def milestone_update(request, project_id, milestone_id):
    def handler(project):
        milestone = get_object_or_404(Milestone, pk=milestone_id, project=project)
        form = MilestoneUpdateForm(request.POST)
        if not form.is_valid():
            raise ValidationError("Datas inválidas.")
        services.update_milestone(
            milestone,
            by=request.user,
            planned_date=form.cleaned_data.get("planned_date"),
            actual_date=form.cleaned_data.get("actual_date"),
        )
        return "Marco atualizado."

    return _post_action(request, project_id, handler)


@require_POST
def milestone_cancel(request, project_id, milestone_id):
    def handler(project):
        milestone = get_object_or_404(Milestone, pk=milestone_id, project=project)
        form = ReasonForm(request.POST)
        if not form.is_valid():
            raise ValidationError("Informe o motivo do cancelamento.")
        services.cancel_milestone(milestone, by=request.user, reason=form.cleaned_data["reason"])
        return "Marco cancelado."

    return _post_action(request, project_id, handler)


@require_POST
def project_submit(request, project_id):
    def handler(project):
        workflow.submit(project, by=request.user)
        return "Projeto submetido para aprovação do Gestor de P&D."

    return _post_action(request, project_id, handler)


def _decision(request, project_id, action):
    project, denied = get_project_or_deny(request, project_id)
    if denied:
        return denied
    try:
        if action == "approve":
            project = workflow.approve(project, by=request.user)
            messages.success(
                request, f"Projeto aprovado: {project.code}, versão {project.version_display}."
            )
        else:
            form = ReturnForm(request.POST)
            comment = form.cleaned_data["comment"] if form.is_valid() else ""
            workflow.return_project(project, by=request.user, comment=comment)
            messages.success(request, "Projeto devolvido ao líder.")
    except ValidationError as exc:
        _errors(request, exc)
    return redirect("projects:detail", project_id=project.pk)


@require_POST
@profile_required(Profile.RD_MANAGER)
def project_approve(request, project_id):
    return _decision(request, project_id, "approve")


@require_POST
@profile_required(Profile.RD_MANAGER)
def project_return(request, project_id):
    return _decision(request, project_id, "return")
