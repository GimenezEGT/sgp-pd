"""Projeto, TAP, Plano de Negócios, previsões, equipe, marcos e decisões (feature 002)."""

from django.conf import settings
from django.db import models
from django.db.models import Q, Sum
from django.utils import timezone

from sgp.core.models import AppendOnlyModel, ProtectedModel, ProtectedQuerySet
from sgp.vocab.models import SUBDOCUMENT_TYPE, TECHNOLOGY, Term


class RegulatoryBody(models.TextChoices):
    ANVISA = "ANVISA", "ANVISA"
    MAPA = "MAPA", "MAPA"


class RiskClass(models.TextChoices):
    I = "I", "I"  # noqa: E741
    II = "II", "II"
    III = "III", "III"
    IV = "IV", "IV"


class ProjectStatus(models.TextChoices):
    DRAFT = "draft", "Rascunho"
    SUBMITTED = "submitted", "Submetido"
    RETURNED = "returned", "Devolvido"
    OPEN = "open", "Aberto"


EDITABLE_STATUSES = frozenset({ProjectStatus.DRAFT, ProjectStatus.RETURNED})
TEAM_EDITABLE_STATUSES = frozenset(
    {ProjectStatus.DRAFT, ProjectStatus.RETURNED, ProjectStatus.OPEN}
)
NOTIFICATION_CLASSES = frozenset({RiskClass.I, RiskClass.II})


class Project(ProtectedModel):
    title = models.CharField("nome do projeto", max_length=200)
    product_name = models.CharField("nome do produto", max_length=200)
    product_family = models.CharField("família", max_length=200, blank=True)
    technology = models.ForeignKey(
        Term,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="tecnologia",
        limit_choices_to={"vocabulary__code": TECHNOLOGY},
    )
    regulatory_body = models.CharField(
        "órgão regulador", max_length=10, choices=RegulatoryBody.choices
    )
    risk_class = models.CharField(
        "classe de risco prevista", max_length=3, choices=RiskClass.choices, blank=True
    )
    classification_rule = models.CharField("regra de classificação", max_length=200, blank=True)
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="led_projects",
        verbose_name="líder",
    )
    status = models.CharField(
        "situação", max_length=10, choices=ProjectStatus.choices, default=ProjectStatus.DRAFT
    )
    code = models.CharField("código", max_length=20, unique=True, null=True, blank=True)
    version = models.PositiveSmallIntegerField("versão", null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    created_at = models.DateTimeField("criado em", default=timezone.now)
    updated_at = models.DateTimeField("alterado em", auto_now=True)
    submitted_at = models.DateTimeField("submetido em", null=True, blank=True)
    approved_at = models.DateTimeField("aprovado em", null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    row_version = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "projeto"
        verbose_name_plural = "projetos"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["status"], name="projects_status"),
            models.Index(fields=["leader", "status"], name="projects_leader_status"),
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.title}" if self.code else f"{self.title} (sem código)"

    @property
    def regime(self) -> str:
        if self.regulatory_body != RegulatoryBody.ANVISA or not self.risk_class:
            return ""
        return "Notificação" if self.risk_class in NOTIFICATION_CLASSES else "Registro"

    @property
    def version_display(self) -> str:
        return f"{self.version:02d}" if self.version else "—"

    @property
    def is_editable(self) -> bool:
        return self.status in EDITABLE_STATUSES

    def is_member(self, user) -> bool:
        """Participação para a regra única de acesso (sgp.core.access.can_access_project)."""
        if user is None or not getattr(user, "is_authenticated", False):
            return False
        if user.pk == self.leader_id:
            return True
        if self.status != ProjectStatus.OPEN:
            return False
        return self.members.active().filter(user_id=user.pk).exists()


class ProjectCharter(ProtectedModel):
    """Termo de Abertura de Projeto (TAP); listas e tabelas em JSONB (sem exclusão de linhas)."""

    project = models.OneToOneField(Project, on_delete=models.PROTECT, related_name="charter")
    justification = models.TextField("justificativa", blank=True)
    objective = models.TextField("objetivo", blank=True)
    scope_included = models.JSONField("escopo incluído", default=list, blank=True)
    scope_excluded = models.JSONField("escopo excluído", default=list, blank=True)
    deliverables = models.JSONField("entregas", default=list, blank=True)
    assumptions = models.JSONField("premissas", default=list, blank=True)
    constraints = models.JSONField("restrições", default=list, blank=True)
    risks = models.JSONField("riscos iniciais", default=list, blank=True)
    stakeholders = models.JSONField("partes interessadas", default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    row_version = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "termo de abertura de projeto"
        verbose_name_plural = "termos de abertura de projeto"

    def __str__(self) -> str:
        return f"TAP — {self.project}"


class BusinessPlan(ProtectedModel):
    """Plano de Negócios; nome do projeto e líder vêm do projeto (fonte única)."""

    project = models.OneToOneField(Project, on_delete=models.PROTECT, related_name="business_plan")
    plan_date = models.DateField("data", null=True, blank=True)
    objective = models.TextField("objetivo", blank=True)
    description = models.TextField("descrição geral", blank=True)
    total_cost = models.DecimalField(
        "custo total do projeto", max_digits=14, decimal_places=2, null=True, blank=True
    )
    execution_months = models.PositiveIntegerField(
        "prazo de execução (meses)", null=True, blank=True
    )
    execution_end_date = models.DateField("término previsto", null=True, blank=True)
    target_market = models.TextField("mercado-alvo", blank=True)
    competitors = models.JSONField("principais concorrentes", default=list, blank=True)
    competitor_price_min = models.DecimalField(
        "preço por teste dos concorrentes (mínimo)",
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
    )
    competitor_price_max = models.DecimalField(
        "preço por teste dos concorrentes (máximo)",
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
    )
    competitor_presentations = models.JSONField(
        "apresentações dos concorrentes", default=list, blank=True
    )
    max_production_cost = models.DecimalField(
        "custo máximo de produção", max_digits=14, decimal_places=2, null=True, blank=True
    )
    sale_price_min = models.DecimalField(
        "preço de venda previsto (mínimo)", max_digits=14, decimal_places=2, null=True, blank=True
    )
    sale_price_max = models.DecimalField(
        "preço de venda previsto (máximo)", max_digits=14, decimal_places=2, null=True, blank=True
    )
    annual_sales_tests = models.PositiveIntegerField(
        "venda anual prevista (testes/ano)", null=True, blank=True
    )
    factory_structure = models.TextField("estrutura fabril", blank=True)
    production_team = models.TextField("equipe de produção", blank=True)
    quality_control = models.TextField("controle de qualidade", blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    row_version = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "plano de negócios"
        verbose_name_plural = "planos de negócios"

    def __str__(self) -> str:
        return f"Plano de Negócios — {self.project}"

    @property
    def forecast_total(self):
        """Retorno total em 5 anos: sempre a soma das previsões (FR-008)."""
        return self.forecasts.aggregate(total=Sum("amount"))["total"]


class AnnualForecast(ProtectedModel):
    business_plan = models.ForeignKey(
        BusinessPlan, on_delete=models.PROTECT, related_name="forecasts"
    )
    year_index = models.PositiveSmallIntegerField("ano")
    amount = models.DecimalField(
        "receita líquida prevista", max_digits=14, decimal_places=2, null=True, blank=True
    )

    class Meta:
        verbose_name = "previsão anual"
        verbose_name_plural = "previsões anuais"
        ordering = ["business_plan", "year_index"]
        constraints = [
            models.UniqueConstraint(
                fields=["business_plan", "year_index"], name="projects_forecast_year"
            ),
            models.CheckConstraint(
                condition=Q(year_index__gte=1) & Q(year_index__lte=5),
                name="projects_forecast_year_range",
            ),
        ]


class MemberQuerySet(ProtectedQuerySet):
    def active(self, on=None):
        on = on or timezone.localdate()
        return self.filter(start_date__lte=on).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=on)
        )


class ProjectMember(ProtectedModel):
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="members")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="memberships"
    )
    role = models.CharField("papel no projeto", max_length=200)
    start_date = models.DateField("início da vigência", default=timezone.localdate)
    end_date = models.DateField("fim da vigência", null=True, blank=True)
    end_reason = models.TextField("motivo do encerramento", blank=True)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    added_at = models.DateTimeField(default=timezone.now)
    ended_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    ended_at = models.DateTimeField(null=True, blank=True)

    objects = MemberQuerySet.as_manager()

    class Meta:
        verbose_name = "membro do projeto"
        verbose_name_plural = "membros do projeto"
        ordering = ["start_date", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "user"],
                condition=Q(end_date__isnull=True),
                name="projects_member_open_unique",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user.get_full_name()} — {self.role}"


class MilestoneQuerySet(ProtectedQuerySet):
    def active(self):
        return self.filter(canceled_at__isnull=True)


class Milestone(ProtectedModel):
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="milestones")
    subdocument_type = models.ForeignKey(
        Term,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="subdocumento",
        limit_choices_to={"vocabulary__code": SUBDOCUMENT_TYPE},
    )
    description = models.CharField("descrição", max_length=200, blank=True)
    planned_date = models.DateField("data planejada")
    actual_date = models.DateField("data realizada", null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    canceled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    cancel_reason = models.TextField("motivo do cancelamento", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    created_at = models.DateTimeField(default=timezone.now)

    objects = MilestoneQuerySet.as_manager()

    class Meta:
        verbose_name = "marco"
        verbose_name_plural = "marcos"
        ordering = ["planned_date", "id"]

    def __str__(self) -> str:
        label = self.subdocument_type.label
        return f"{label} — {self.description}" if self.description else label


class DecisionAction(models.TextChoices):
    SUBMITTED = "submitted", "Submetido"
    RETURNED = "returned", "Devolvido"
    APPROVED = "approved", "Aprovado"


class ProjectDecision(AppendOnlyModel):
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="decisions")
    action = models.CharField("decisão", max_length=10, choices=DecisionAction.choices)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    occurred_at = models.DateTimeField("data e hora", default=timezone.now)
    comment = models.TextField("comentário", blank=True)

    class Meta:
        verbose_name = "decisão do projeto"
        verbose_name_plural = "decisões do projeto"
        ordering = ["occurred_at", "id"]


class ProjectCodeSequence(ProtectedModel):
    year = models.PositiveIntegerField("ano", primary_key=True)
    last_value = models.PositiveIntegerField("último número", default=0)

    class Meta:
        verbose_name = "sequência de código de projeto"
        verbose_name_plural = "sequências de código de projeto"
