"""Pendências que impedem a submissão do projeto (FR-012; data-model "Pendências para submeter")."""

from .models import Project, RegulatoryBody


def _missing_text(value) -> bool:
    return not (value or "").strip()


def pending_items(project: Project) -> list[str]:
    items: list[str] = []
    for field, label in (
        ("title", "nome do projeto"),
        ("product_name", "nome do produto"),
    ):
        if _missing_text(getattr(project, field)):
            items.append(f"Produto: informe o {label}.")
    if project.regulatory_body == RegulatoryBody.ANVISA:
        if not project.risk_class:
            items.append("Produto: informe a classe de risco prevista.")
        if _missing_text(project.classification_rule):
            items.append("Produto: informe a regra de classificação.")

    charter = project.charter
    for field, label in (("justification", "a justificativa"), ("objective", "o objetivo")):
        if _missing_text(getattr(charter, field)):
            items.append(f"TAP: informe {label}.")
    for field, label in (
        ("scope_included", "um item de escopo incluído"),
        ("deliverables", "uma entrega"),
        ("risks", "um risco inicial"),
        ("stakeholders", "uma parte interessada"),
    ):
        if not getattr(charter, field):
            items.append(f"TAP: inclua ao menos {label}.")
    if not project.milestones.active().exists():
        items.append("TAP: inclua ao menos um marco com data planejada.")

    plan = project.business_plan
    if plan.plan_date is None:
        items.append("Plano de Negócios: informe a data.")
    for field, label in (
        ("objective", "o objetivo"),
        ("description", "a descrição geral"),
        ("target_market", "o mercado-alvo"),
        ("factory_structure", "a avaliação da estrutura fabril"),
        ("production_team", "a avaliação da equipe de produção"),
        ("quality_control", "a avaliação do controle de qualidade"),
    ):
        if _missing_text(getattr(plan, field)):
            items.append(f"Plano de Negócios: informe {label}.")
    for field, label in (
        ("total_cost", "o custo total"),
        ("competitor_price_min", "o preço mínimo dos concorrentes"),
        ("competitor_price_max", "o preço máximo dos concorrentes"),
        ("max_production_cost", "o custo máximo de produção"),
        ("sale_price_min", "o preço mínimo de venda previsto"),
        ("sale_price_max", "o preço máximo de venda previsto"),
        ("annual_sales_tests", "a venda anual prevista"),
    ):
        if getattr(plan, field) is None:
            items.append(f"Plano de Negócios: informe {label}.")
    if plan.execution_months is None and plan.execution_end_date is None:
        items.append("Plano de Negócios: informe o prazo de execução (meses ou término).")
    if not plan.competitors:
        items.append("Plano de Negócios: inclua ao menos um concorrente.")
    if not plan.competitor_presentations:
        items.append("Plano de Negócios: inclua ao menos uma apresentação dos concorrentes.")
    missing_years = [str(f.year_index) for f in plan.forecasts.all() if f.amount is None]
    if missing_years:
        items.append(
            f"Plano de Negócios: informe o retorno esperado dos anos {', '.join(missing_years)}."
        )
    return items
