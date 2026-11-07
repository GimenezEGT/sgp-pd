"""Criação e edição de projeto, TAP, Plano de Negócios, equipe e marcos (FR-001 a FR-010,
FR-017, FR-019, FR-020). Toda mudança grava o evento na mesma transação."""

from datetime import date

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from sgp.accounts.profiles import Profile, active_profiles
from sgp.audit.services import record_event
from sgp.core.diff import changed_fields

from .models import (
    EDITABLE_STATUSES,
    AnnualForecast,
    BusinessPlan,
    Milestone,
    Project,
    ProjectCharter,
    ProjectMember,
    ProjectStatus,
    RegulatoryBody,
)

PRODUCT_FIELDS = (
    "title",
    "product_name",
    "product_family",
    "technology",
    "regulatory_body",
    "risk_class",
    "classification_rule",
)
CHARTER_FIELDS = (
    "justification",
    "objective",
    "scope_included",
    "scope_excluded",
    "deliverables",
    "assumptions",
    "constraints",
    "risks",
    "stakeholders",
)
PLAN_FIELDS = (
    "plan_date",
    "objective",
    "description",
    "total_cost",
    "execution_months",
    "execution_end_date",
    "target_market",
    "competitors",
    "competitor_price_min",
    "competitor_price_max",
    "competitor_presentations",
    "max_production_cost",
    "sale_price_min",
    "sale_price_max",
    "annual_sales_tests",
    "factory_structure",
    "production_team",
    "quality_control",
)
STALE_MESSAGE = "Outra pessoa gravou este documento depois que você o abriu; recarregue a página."


# ------------------------------------------------------------------- utilidades


def _event(event_type: str, project: Project, by, **kwargs):
    return record_event(event_type, actor=by, project_id=project.pk, **kwargs)


def _check_version(current: int, expected) -> None:
    if expected is not None and int(expected) != current:
        raise ValidationError(STALE_MESSAGE)


def _require_leader(project: Project, by) -> None:
    if project.leader_id != by.pk:
        raise ValidationError("Só o líder do projeto pode alterar este conteúdo.")


def _require_document_editable(project: Project, document) -> None:
    """TAP e Plano: editáveis em rascunho/devolvido do projeto ou em nova versão já aberto."""
    if project.status == ProjectStatus.OPEN:
        if document.doc_status not in ("draft", "returned"):
            raise ValidationError(
                "Documento aprovado não muda; crie uma nova versão com motivo para corrigir."
            )
        return
    _require_editable(project)


def _require_editable(project: Project) -> None:
    if project.status not in EDITABLE_STATUSES:
        raise ValidationError(
            f"O projeto está {ProjectStatus(project.status).label.lower()} e não pode ser editado."
        )


def _product_snapshot(project: Project) -> dict:
    data = {field: getattr(project, field) for field in PRODUCT_FIELDS if field != "technology"}
    data["technology"] = project.technology.label if project.technology_id else ""
    return data


def _normalize_product(data: dict) -> dict:
    data = dict(data)
    if data.get("regulatory_body") == RegulatoryBody.MAPA:
        data["risk_class"] = ""
        data["classification_rule"] = ""
    return data


# --------------------------------------------------------------------- projeto


def create_project(*, by, data: dict, leader=None) -> Project:
    profiles = active_profiles(by)
    if not profiles & {Profile.PROJECT_LEADER, Profile.RD_MANAGER}:
        raise ValidationError("Só o Líder de projeto ou o Gestor de P&D criam projetos.")
    if leader is None:
        if Profile.PROJECT_LEADER not in profiles:
            raise ValidationError("Indique o líder do projeto.")
        leader = by
    elif Profile.PROJECT_LEADER not in active_profiles(leader):
        raise ValidationError("O líder indicado precisa ter o perfil Líder de projeto.")
    data = _normalize_product(data)
    with transaction.atomic():
        project = Project.objects.create(leader=leader, created_by=by, **data)
        ProjectCharter.objects.create(project=project)
        plan = BusinessPlan.objects.create(project=project)
        AnnualForecast.objects.bulk_create(
            [AnnualForecast(business_plan=plan, year_index=year) for year in range(1, 6)]
        )
        ProjectMember.objects.create(
            project=project, user=leader, role="Líder do projeto", added_by=by
        )
        _event(
            "projects.created",
            project,
            by,
            obj=project,
            new_value={**_product_snapshot(project), "lider": leader.username},
        )
    return project


def update_product(project: Project, *, by, data: dict, row_version=None) -> Project:
    data = _normalize_product(data)
    with transaction.atomic():
        project = Project.objects.select_for_update().get(pk=project.pk)
        _require_leader(project, by)
        _require_editable(project)
        _check_version(project.row_version, row_version)
        before = _product_snapshot(project)
        for field, value in data.items():
            setattr(project, field, value)
        project.row_version += 1
        project.save()
        old, new = changed_fields(before, _product_snapshot(project))
        if new:
            _event("projects.updated", project, by, obj=project, old_value=old, new_value=new)
    return project


# ------------------------------------------------------------------------- TAP


def _charter_snapshot(charter: ProjectCharter) -> dict:
    return {field: getattr(charter, field) for field in CHARTER_FIELDS}


def update_charter(project: Project, *, by, data: dict, row_version=None) -> ProjectCharter:
    with transaction.atomic():
        project = Project.objects.select_for_update().get(pk=project.pk)
        _require_leader(project, by)
        charter = ProjectCharter.objects.select_for_update().get(project=project)
        _require_document_editable(project, charter)
        _check_version(charter.row_version, row_version)
        before = _charter_snapshot(charter)
        for field in CHARTER_FIELDS:
            if field in data:
                setattr(charter, field, data[field])
        charter.updated_by = by
        charter.row_version += 1
        charter.save()
        old, new = changed_fields(before, _charter_snapshot(charter))
        if new:
            _event(
                "projects.charter_updated", project, by, obj=charter, old_value=old, new_value=new
            )
    return charter


# ------------------------------------------------------------- Plano de Negócios


def _plan_snapshot(plan: BusinessPlan) -> dict:
    data = {field: getattr(plan, field) for field in PLAN_FIELDS}
    data["forecasts"] = {str(f.year_index): f.amount for f in plan.forecasts.order_by("year_index")}
    data["forecast_total"] = plan.forecast_total
    return data


def _validate_plan(data: dict) -> None:
    errors = []
    for low, high, label in (
        ("competitor_price_min", "competitor_price_max", "preço dos concorrentes"),
        ("sale_price_min", "sale_price_max", "preço de venda previsto"),
    ):
        if data.get(low) is not None and data.get(high) is not None and data[low] > data[high]:
            errors.append(f"Na faixa de {label}, o mínimo não pode ser maior que o máximo.")
    for field in PLAN_FIELDS + ("forecasts",):
        value = data.get(field)
        values = value.values() if isinstance(value, dict) else [value]
        if any(v is not None and not isinstance(v, str | list | date) and v < 0 for v in values):
            errors.append("Valores não podem ser negativos.")
            break
    if errors:
        raise ValidationError(errors)


def update_business_plan(
    project: Project, *, by, data: dict, forecasts: dict[int, object], row_version=None
) -> BusinessPlan:
    _validate_plan({**data, "forecasts": forecasts})
    with transaction.atomic():
        project = Project.objects.select_for_update().get(pk=project.pk)
        _require_leader(project, by)
        plan = BusinessPlan.objects.select_for_update().get(project=project)
        _require_document_editable(project, plan)
        _check_version(plan.row_version, row_version)
        before = _plan_snapshot(plan)
        for field in PLAN_FIELDS:
            if field in data:
                setattr(plan, field, data[field])
        plan.updated_by = by
        plan.row_version += 1
        plan.save()
        for forecast in plan.forecasts.select_for_update():
            if forecast.year_index in forecasts:
                forecast.amount = forecasts[forecast.year_index]
                forecast.save(update_fields=["amount"])
        old, new = changed_fields(before, _plan_snapshot(plan))
        if new:
            _event(
                "projects.business_plan_updated",
                project,
                by,
                obj=plan,
                old_value=old,
                new_value=new,
            )
    return plan


# ----------------------------------------------------------------------- equipe


def _require_team_editable(project: Project, by) -> None:
    _require_leader(project, by)
    if project.status == ProjectStatus.SUBMITTED:
        raise ValidationError("O projeto está submetido e a equipe não pode ser alterada.")


def add_member(
    project: Project, *, by, user, role: str, start_date: date | None = None
) -> ProjectMember:
    role = (role or "").strip()
    if not role:
        raise ValidationError("Informe o papel no projeto.")
    if not user.is_active:
        raise ValidationError("Pessoa desativada não entra na equipe.")
    start_date = start_date or timezone.localdate()
    try:
        with transaction.atomic():
            project = Project.objects.select_for_update().get(pk=project.pk)
            _require_team_editable(project, by)
            member = ProjectMember.objects.create(
                project=project, user=user, role=role, start_date=start_date, added_by=by
            )
            _event(
                "projects.member_added",
                project,
                by,
                obj=member,
                new_value={"pessoa": user.username, "papel": role, "inicio": start_date},
            )
    except IntegrityError as exc:
        raise ValidationError("A pessoa já faz parte da equipe.") from exc
    return member


def end_member(
    member: ProjectMember, *, by, reason: str, end_date: date | None = None
) -> ProjectMember:
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError("Informe o motivo do encerramento.")
    end_date = end_date or timezone.localdate()
    with transaction.atomic():
        project = Project.objects.select_for_update().get(pk=member.project_id)
        _require_team_editable(project, by)
        member = ProjectMember.objects.select_for_update().get(pk=member.pk)
        if member.end_date is not None:
            raise ValidationError("A vigência deste membro já foi encerrada.")
        if member.user_id == project.leader_id:
            raise ValidationError("A vigência do líder do projeto não pode ser encerrada.")
        if end_date < member.start_date:
            raise ValidationError("O fim da vigência não pode ser anterior ao início.")
        member.end_date = end_date
        member.end_reason = reason
        member.ended_by = by
        member.ended_at = timezone.now()
        member.save(update_fields=["end_date", "end_reason", "ended_by", "ended_at"])
        _event(
            "projects.member_ended",
            project,
            by,
            obj=member,
            old_value={"fim": None},
            new_value={"pessoa": member.user.username, "fim": end_date},
            reason=reason,
        )
    return member


# ------------------------------------------------------------------------ marcos


def add_milestone(
    project: Project, *, by, subdocument_type, planned_date: date, description: str = ""
) -> Milestone:
    if planned_date is None:
        raise ValidationError("Informe a data planejada.")
    with transaction.atomic():
        project = Project.objects.select_for_update().get(pk=project.pk)
        _require_leader(project, by)
        _require_editable(project)
        milestone = Milestone.objects.create(
            project=project,
            subdocument_type=subdocument_type,
            description=(description or "").strip(),
            planned_date=planned_date,
            created_by=by,
        )
        _event(
            "projects.milestone_added",
            project,
            by,
            obj=milestone,
            new_value={"subdocumento": subdocument_type.label, "data_planejada": planned_date},
        )
    return milestone


def update_milestone(
    milestone: Milestone, *, by, planned_date: date | None = None, actual_date: date | None = None
) -> Milestone:
    with transaction.atomic():
        project = Project.objects.select_for_update().get(pk=milestone.project_id)
        _require_leader(project, by)
        milestone = Milestone.objects.select_for_update().get(pk=milestone.pk)
        if milestone.canceled_at is not None:
            raise ValidationError("O marco está cancelado.")
        before = {"data_planejada": milestone.planned_date, "data_realizada": milestone.actual_date}
        if planned_date is not None and planned_date != milestone.planned_date:
            _require_editable(project)
            milestone.planned_date = planned_date
        if actual_date is not None:
            if project.status != ProjectStatus.OPEN:
                raise ValidationError(
                    "A data realizada só é informada depois que o projeto é aberto."
                )
            if actual_date > timezone.localdate():
                raise ValidationError("A data realizada não pode estar no futuro.")
            if actual_date < timezone.localtime(project.created_at).date():
                raise ValidationError(
                    "A data realizada não pode ser anterior à criação do projeto."
                )
            milestone.actual_date = actual_date
        milestone.save(update_fields=["planned_date", "actual_date"])
        after = {"data_planejada": milestone.planned_date, "data_realizada": milestone.actual_date}
        old, new = changed_fields(before, after)
        if new:
            _event(
                "projects.milestone_updated",
                project,
                by,
                obj=milestone,
                old_value=old,
                new_value=new,
            )
    return milestone


def cancel_milestone(milestone: Milestone, *, by, reason: str) -> Milestone:
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError("Informe o motivo do cancelamento.")
    with transaction.atomic():
        project = Project.objects.select_for_update().get(pk=milestone.project_id)
        _require_leader(project, by)
        _require_editable(project)
        milestone = Milestone.objects.select_for_update().get(pk=milestone.pk)
        if milestone.canceled_at is not None:
            raise ValidationError("O marco já foi cancelado.")
        milestone.canceled_at = timezone.now()
        milestone.canceled_by = by
        milestone.cancel_reason = reason
        milestone.save(update_fields=["canceled_at", "canceled_by", "cancel_reason"])
        _event("projects.milestone_canceled", project, by, obj=milestone, reason=reason)
    return milestone


# ------------------------------------------------------------- versão do projeto


def bump_version(project: Project, *, by, reason: str) -> Project:
    """Alteração de Projeto aprovada (feature 004): a versão do projeto sobe, com evento."""
    with transaction.atomic():
        project = Project.objects.select_for_update().get(pk=project.pk)
        before = project.version_display
        project.version = (project.version or 0) + 1
        project.row_version += 1
        project.save(update_fields=["version", "row_version", "updated_at"])
        _event(
            "projects.version_changed",
            project,
            by,
            obj=project,
            old_value={"versao": before},
            new_value={"versao": project.version_display},
            reason=reason,
        )
    return project
