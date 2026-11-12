"""Ordem recomendada dos subdocumentos e pré-requisitos (FR-016, FR-019 da feature 004).

A Entrada aprovada é pré-requisito de todos os outros, sem dispensa (RDC 665/2022, art. 46).
Nos demais passos o antecessor aprovado é recomendado: faltando, o Gestor de P&D autoriza.
"""

from dataclasses import dataclass

from .models import CHANGE, ENTRY, Subdocument, SubdocumentStatus

FLOW = (
    "entrada",
    "formulacao",
    "lote-piloto",
    "rapd",
    "analise-critica",
    "validacao",
    "verificacao-final",
    "saida",
)


@dataclass(frozen=True)
class Requirement:
    missing: str
    overridable: bool


def approved(project, code: str) -> Subdocument | None:
    """Subdocumento do tipo com versão aprovada (aprovado agora ou com versão anterior aprovada)."""
    from sgp.signatures.models import ApprovedVersion

    candidates = Subdocument.objects.filter(project=project, subdocument_type__code=code).order_by(
        "-sequence"
    )
    for candidate in candidates:
        if (
            candidate.status == SubdocumentStatus.APPROVED
            or ApprovedVersion.objects.filter(kind="subdocument", object_id=candidate.pk).exists()
        ):
            return candidate
    return None


def approved_content(subdocument):
    """(modelo, tópicos) da última versão aprovada; o rascunho de versão nova não conta."""
    from sgp.formtemplates.models import FormTemplate
    from sgp.signatures.models import ApprovedVersion

    if subdocument.status == SubdocumentStatus.APPROVED:
        return subdocument.template, (subdocument.data or {}).get("topics", {})
    latest = (
        ApprovedVersion.objects.filter(kind="subdocument", object_id=subdocument.pk)
        .order_by("-version")
        .first()
    )
    if latest is None:
        return subdocument.template, (subdocument.data or {}).get("topics", {})
    template = FormTemplate.objects.get(pk=latest.content["modelo"]["id"])
    return template, latest.content.get("topicos", {})


def _label(code: str) -> str:
    from sgp.vocab.models import get_term

    return get_term("tipo-subdocumento", code).label


def requirement(project, code: str) -> Requirement | None:
    """O que falta para criar o subdocumento do tipo `code` (None quando nada falta)."""
    if code == ENTRY:
        return None
    if approved(project, ENTRY) is None:
        return Requirement(f"{_label(ENTRY)} aprovada", overridable=False)
    if code == CHANGE:
        return None
    if code not in FLOW:
        return None
    previous = FLOW[FLOW.index(code) - 1]
    if previous != ENTRY and approved(project, previous) is None:
        return Requirement(f"{_label(previous)} aprovada", overridable=True)
    return None
