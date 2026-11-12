"""Classe de risco, família e checagem item a item (FR-001, FR-003, FR-009; research R3 e R7)."""

from sgp.projects.models import Project

from . import definition, sources
from .sources import COMPLETE, MISSING, NOT_APPLICABLE, STATUS_LABELS


def risk_class(project) -> str | None:
    versions = sources.approved_versions(project, "entrada")
    if not versions:
        return None
    _, approval = versions[-1]
    topic = ((approval.content or {}).get("topicos") or {}).get("classificacao_risco") or {}
    value = str((topic.get("values") or {}).get("classe") or "").strip().upper()
    return value if value in definition.CLASSES else None


def family(project) -> list[Project]:
    """Projetos da mesma família, tecnologia e classe (ou só o projeto)."""
    if not (project.product_family or "").strip():
        return [project]
    own_class = risk_class(project)
    kits = []
    for candidate in Project.objects.filter(
        product_family__iexact=project.product_family.strip(),
        technology=project.technology,
    ).order_by("code", "pk"):
        if candidate.pk == project.pk or risk_class(candidate) == own_class:
            kits.append(candidate)
    return kits


def subject(project) -> str:
    kits = family(project)
    if len(kits) > 1:
        return f"Família {project.product_family.strip()}"
    return project.code or f"Projeto {project.pk}"


def _combine(parts) -> dict:
    statuses = [part.status for part in parts]
    if MISSING in statuses:
        status = MISSING
    elif all(s == NOT_APPLICABLE for s in statuses):
        status = NOT_APPLICABLE
    else:
        status = COMPLETE
    blocks, annexes, used, reasons, justifications = [], [], [], [], []
    for part in parts:
        blocks += part.blocks
        annexes += part.annexes
        used += part.used
        if part.reason:
            reasons.append(part.reason)
        if part.justification:
            justifications.append(part.justification)
            if status == COMPLETE:
                blocks.append({"kind": "note", "text": f"Não aplicável: {part.justification}"})
    return {
        "status": status,
        "origin": "; ".join(dict.fromkeys(part.origin for part in parts)),
        "blocks": blocks,
        "annexes": annexes,
        "used": used,
        "reason": " ".join(reasons),
        "justification": "; ".join(justifications),
    }


def evaluate(project, parsed: dict) -> dict:
    """Checagem completa: classe, kits e cada item final com situação, origem e conteúdo."""
    kits = family(project)
    klass = risk_class(project)
    items = []
    for item, parents in definition.leaves(parsed["itens"]):
        path = [*parents, item]
        entry = {
            "key": item["key"],
            "path": [{"numero": node["numero"], "titulo": node["titulo"]} for node in path],
            "titulo": item["titulo"],
            "level": len(path),
        }
        if klass is None:
            entry.update(
                status=MISSING,
                origin="Entrada de Projeto › Classificação de Risco",
                reason="Classe de risco não definida na Entrada aprovada.",
                blocks=[],
                annexes=[],
                used=[],
                justification="",
            )
            items.append(entry)
            continue
        applies, outside = definition.applies(item, parents, klass)
        if not applies:
            entry.update(
                status=NOT_APPLICABLE,
                origin=f"Definição do dossiê (classe {klass})",
                reason="",
                blocks=[],
                annexes=[],
                used=[],
                justification=outside,
            )
            items.append(entry)
            continue
        per_kit = []
        for kit in kits:
            parts = [sources.evaluate(kit, source, item["key"]) for source in item["fontes"]]
            combined = _combine(parts)
            per_kit.append((kit, combined))
        if len(per_kit) == 1:
            entry.update(per_kit[0][1])
        else:
            statuses = [c["status"] for _, c in per_kit]
            status = (
                MISSING
                if MISSING in statuses
                else (NOT_APPLICABLE if all(s == NOT_APPLICABLE for s in statuses) else COMPLETE)
            )
            blocks, annexes, used, reasons, justifications = [], [], [], [], []
            for kit, combined in per_kit:
                blocks.append({"kind": "values", "label": "Kit", "lines": [kit.product_name]})
                blocks += combined["blocks"]
                if combined["status"] == NOT_APPLICABLE:
                    blocks.append(
                        {"kind": "note", "text": f"Não aplicável: {combined['justification']}"}
                    )
                annexes += combined["annexes"]
                used += combined["used"]
                if combined["reason"]:
                    reasons.append(f"{kit.product_name}: {combined['reason']}")
                if combined["justification"]:
                    justifications.append(f"{kit.product_name}: {combined['justification']}")
            entry.update(
                status=status,
                origin=per_kit[0][1]["origin"],
                blocks=blocks,
                annexes=annexes,
                used=used,
                reason=" ".join(reasons),
                justification="; ".join(justifications),
            )
        items.append(entry)
    for entry in items:
        entry["status_label"] = STATUS_LABELS[entry["status"]]
    missing = [entry for entry in items if entry["status"] == MISSING]
    return {
        "risk_class": klass,
        "kits": kits,
        "items": items,
        "missing": missing,
        "complete": not missing,
    }
