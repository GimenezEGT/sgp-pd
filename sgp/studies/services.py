"""Estudos com cálculo automático (FR-001 a FR-018 da feature 007).

Linhas validadas contra os cadastros (fonte única), critério congelado depois da primeira linha,
resultados recalculados a cada gravação em elaboração, "não aplicável" com justificativa, bloqueio
na aprovação do subdocumento vinculado e nova versão com motivo.
"""

from decimal import Decimal, InvalidOperation

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from sgp.audit.services import record_event
from sgp.catalog.kinds import get_kind
from sgp.core.access import can_access_project
from sgp.formtemplates.fieldtypes import parse_number

from . import profiles
from .models import Study, StudyStatus

STUDY_VOCABULARY = "tipo-estudo"
LINKABLE_TYPES = ("rapd", "validacao")
COLUMNS = (
    "amostra",
    "lote",
    "kit",
    "dia",
    "corrida",
    "replicata",
    "grupo",
    "x",
    "y",
    "esperado",
    "obtido",
)
REFERENCES = {
    "amostra": ("amostras", "identifier"),
    "lote": ("lotes", "code"),
    "kit": ("kits", "lot"),
}
INTEGERS = ("dia", "corrida", "replicata")
NUMBERS = ("x", "y")
QUALITATIVE = {
    "pos": "pos",
    "positivo": "pos",
    "p": "pos",
    "reagente": "pos",
    "neg": "neg",
    "negativo": "neg",
    "n": "neg",
    "não reagente": "neg",
    "nao reagente": "neg",
}
NOT_EDITABLE = "Estudo bloqueado por documento aprovado: crie nova versão com motivo."
NO_PROFILE = "Tipo de estudo sem cálculo definido; avise a Qualidade."


# ------------------------------------------------------------------ permissões e apoio


def can_edit(user, project) -> bool:
    from sgp.subdocuments.permissions import can_edit as can_edit_project

    return can_edit_project(user, project)


def can_view(user, project) -> bool:
    return can_access_project(user, project)


def profile_of(study_type) -> profiles.Profile:
    profile = profiles.PROFILES.get(study_type.code)
    if profile is None:
        raise ValidationError(NO_PROFILE)
    return profile


def _event(event_type, study, by, **kwargs):
    return record_event(
        event_type,
        actor=by,
        obj=study,
        project_id=study.project_id,
        object_repr=str(study)[:255],
        **kwargs,
    )


def _require_editable(study, by):
    if not can_edit(by, study.project):
        raise PermissionDenied("Você não pode alterar estudos deste projeto.")
    if study.is_locked:
        raise ValidationError(NOT_EDITABLE)


def _validate_link(project, subdocument, topic_key):
    if subdocument is None:
        return None, ""
    if (
        subdocument.project_id != project.pk
        or subdocument.subdocument_type.code not in LINKABLE_TYPES
    ):
        raise ValidationError(
            "O estudo só alimenta o RAPD ou a Validação do Produto do mesmo projeto."
        )
    if not subdocument.template.topic(topic_key):
        raise ValidationError("Escolha um tópico do subdocumento vinculado.")
    return subdocument, topic_key


def recalc(study) -> dict:
    if study.not_applicable:
        return {}
    results = profiles.compute(study.study_type.code, study.rows, study.config)
    results["criterios"] = profiles.evaluate(study.criteria, results)
    return results


# ------------------------------------------------------------------ criação e configuração


def create_study(project, *, by, data: dict) -> Study:
    if not can_edit(by, project):
        raise PermissionDenied("Você não pode criar estudos neste projeto.")
    study_type = data["study_type"]
    if study_type.vocabulary.code != STUDY_VOCABULARY or not study_type.is_active:
        raise ValidationError("Escolha o tipo de estudo na lista controlada.")
    profile_of(study_type)
    title = (data.get("title") or "").strip()
    if not title:
        raise ValidationError("Informe o título do estudo.")
    subdocument, topic_key = _validate_link(
        project, data.get("subdocument"), data.get("topic_key", "")
    )
    with transaction.atomic():
        study = Study.objects.create(
            project=project,
            study_type=study_type,
            title=title,
            subdocument=subdocument,
            topic_key=topic_key,
            rounding=data.get("rounding") or "half_even",
            ci_method=data.get("ci_method") or "clopper_pearson",
            cutoff=data.get("cutoff"),
            cutoff_direction=data.get("cutoff_direction") or "ge",
            created_by=by,
        )
        study.results = recalc(study)
        study.save(update_fields=["results"])
        _event(
            "studies.created",
            study,
            by,
            new_value={
                "tipo": study_type.label,
                "titulo": title,
                "subdocumento": subdocument.pk if subdocument else None,
                "topico": topic_key,
            },
        )
    return study


def set_criteria(study, *, by, criteria: list[dict]) -> Study:
    _require_editable(study, by)
    if study.rows:
        raise ValidationError(
            "O critério de aceitação não muda depois do primeiro resultado lançado."
        )
    profile = profile_of(study.study_type)
    clean = []
    for index, criterion in enumerate(criteria, start=1):
        metric = criterion.get("metrica")
        comparison = criterion.get("comparacao")
        if metric not in profile.criteria or comparison not in profiles.COMPARISONS:
            raise ValidationError(f"Critério {index}: escolha a métrica e a comparação.")
        try:
            limit = parse_number(str(criterion.get("limite", "")))
        except ValueError as exc:
            raise ValidationError(f"Critério {index}: {exc}") from exc
        if limit is None:
            raise ValidationError(f"Critério {index}: informe o limite.")
        clean.append({"metrica": metric, "comparacao": comparison, "limite": str(limit)})
    with transaction.atomic():
        study = Study.objects.select_for_update().get(pk=study.pk)
        before = study.criteria
        study.criteria = clean
        study.results = recalc(study)
        study.updated_by, study.updated_at = by, timezone.now()
        study.row_version += 1
        study.save()
        _event(
            "studies.criteria_set",
            study,
            by,
            old_value={"criterios": before},
            new_value={"criterios": clean},
        )
    return study


# ------------------------------------------------------------------ linhas


def _reference(column, code, project):
    slug, field = REFERENCES[column]
    kind = get_kind(slug)
    queryset = kind.model.objects.available().filter(**{field: code})
    if kind.project_scoped:
        queryset = queryset.filter(project=project)
    record = queryset.order_by("-version").first()
    if record is None:
        raise ValueError(f"{profiles.COLUMN_LABELS[column]} {code!r} não existe no cadastro.")
    return {"id": record.pk, "codigo": code}


def normalize_rows(study, raw_rows: list[dict]) -> tuple[list[dict], list[str]]:
    """Linhas validadas (cadastros, números, inteiros, qualitativos, colunas obrigatórias)."""
    profile = profile_of(study.study_type)
    rows, errors = [], []
    for line, raw in enumerate(raw_rows, start=1):
        row, problems = {}, []
        for column in profile.columns:
            text = str(raw.get(column) or "").strip()
            if not text:
                continue
            try:
                if column in REFERENCES:
                    row[column] = _reference(column, text, study.project)
                elif column in INTEGERS:
                    row[column] = int(text)
                elif column in NUMBERS:
                    number = parse_number(text) if "," in text or "." not in text else Decimal(text)
                    row[column] = str(number)
                elif column in ("esperado", "obtido"):
                    if text.lower() not in QUALITATIVE:
                        raise ValueError("use positivo ou negativo.")
                    row[column] = QUALITATIVE[text.lower()]
                else:
                    row[column] = text[:120]
            except (ValueError, InvalidOperation) as exc:
                problems.append(f"{profiles.COLUMN_LABELS[column]}: {exc}")
        missing = [profiles.COLUMN_LABELS[c] for c in profile.required if c not in row]
        if missing:
            problems.append("falta " + ", ".join(missing))
        if problems:
            errors.append(f"Linha {line}: " + "; ".join(problems))
        else:
            rows.append(row)
    return rows, errors


def save_rows(study, *, by, raw_rows: list[dict], row_version=None) -> Study:
    _require_editable(study, by)
    if study.not_applicable and raw_rows:
        raise ValidationError(
            "Estudo não aplicável não tem resultados; desmarque o não aplicável antes."
        )
    rows, errors = normalize_rows(study, raw_rows)
    if errors:
        raise ValidationError(errors)
    with transaction.atomic():
        study = Study.objects.select_for_update().get(pk=study.pk)
        if study.is_locked:
            raise ValidationError(NOT_EDITABLE)
        if row_version is not None and int(row_version) != study.row_version:
            raise ValidationError(
                "Outra pessoa gravou este estudo depois que você o abriu; recarregue a página."
            )
        before = len(study.rows)
        study.rows = rows
        study.results = recalc(study)
        study.updated_by, study.updated_at = by, timezone.now()
        study.row_version += 1
        study.save()
        _event(
            "studies.updated",
            study,
            by,
            old_value={"linhas": before},
            new_value={"linhas": len(rows), "resultados": summary(study)},
        )
    return study


def summary(study) -> dict:
    return {
        item["metrica"]: item["arredondado"]
        for item in (study.results or {}).get("global", [])
        if item["metrica"] != "n"
    }


def mark_not_applicable(study, *, by, justification: str, value: bool = True) -> Study:
    _require_editable(study, by)
    justification = (justification or "").strip()
    if value and not justification:
        raise ValidationError("Informe a justificativa do não aplicável.")
    if value and study.rows:
        raise ValidationError("Estudo com resultados lançados não é marcado como não aplicável.")
    with transaction.atomic():
        study = Study.objects.select_for_update().get(pk=study.pk)
        study.not_applicable = value
        study.justification = justification if value else ""
        study.results = recalc(study)
        study.updated_by, study.updated_at = by, timezone.now()
        study.row_version += 1
        study.save()
        _event(
            "studies.not_applicable",
            study,
            by,
            new_value={"nao_aplicavel": value},
            reason=justification,
        )
    return study


# ------------------------------------------------------------------ documentos e versões


def linked_studies(subdocument, topic_key: str | None = None) -> list[Study]:
    """De cada linhagem vinculada ao subdocumento, a versão mais recente."""
    queryset = Study.objects.filter(subdocument=subdocument).select_related("study_type")
    if topic_key is not None:
        queryset = queryset.filter(topic_key=topic_key)
    latest = {}
    for study in queryset.order_by("lineage", "-version"):
        latest.setdefault(study.lineage, study)
    return sorted(latest.values(), key=lambda s: (s.topic_key, s.title, s.pk))


def canonical(study) -> dict:
    """Conteúdo do estudo que entra no resumo assinado do subdocumento (FR-015)."""
    results = {k: v for k, v in (study.results or {}).items() if k != "calculado_em"}
    return {
        "linhagem": str(study.lineage),
        "versao": study.version,
        "tipo": study.study_type.code,
        "titulo": study.title,
        "topico": study.topic_key,
        "nao_aplicavel": study.not_applicable,
        "justificativa": study.justification,
        "configuracao": study.config,
        "criterios": study.criteria,
        "linhas": study.rows,
        "resultados": results,
    }


def lock_for(subdocument, *, by) -> int:
    """Na aprovação do subdocumento: bloqueia os estudos vinculados (FR-015)."""
    count = 0
    for study in linked_studies(subdocument):
        if study.is_locked:
            continue
        Study.objects.filter(pk=study.pk).update(
            status=StudyStatus.LOCKED, locked_by=by, locked_at=timezone.now()
        )
        _event(
            "studies.locked",
            study,
            by,
            new_value={"versao": study.version_display, "subdocumento": subdocument.pk},
        )
        count += 1
    return count


def new_version(study, *, by, reason: str) -> Study:
    if not can_edit(by, study.project):
        raise PermissionDenied("Você não pode alterar estudos deste projeto.")
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError("Informe o motivo da nova versão.")
    if not study.is_locked:
        raise ValidationError(
            "Só estudo bloqueado ganha nova versão; corrija a versão em elaboração."
        )
    with transaction.atomic():
        top = Study.objects.filter(lineage=study.lineage).aggregate(top=Max("version"))["top"]
        if top != study.version:
            raise ValidationError("Já existe versão mais nova deste estudo.")
        copy = Study.objects.create(
            lineage=study.lineage,
            version=top + 1,
            project=study.project,
            study_type=study.study_type,
            title=study.title,
            subdocument=study.subdocument,
            topic_key=study.topic_key,
            rounding=study.rounding,
            places=study.places,
            fine_places=study.fine_places,
            ci_method=study.ci_method,
            cutoff=study.cutoff,
            cutoff_direction=study.cutoff_direction,
            criteria=study.criteria,
            rows=study.rows,
            not_applicable=study.not_applicable,
            justification=study.justification,
            version_reason=reason,
            created_by=by,
        )
        copy.results = recalc(copy)
        copy.save(update_fields=["results"])
        _event(
            "studies.new_version",
            copy,
            by,
            old_value={"versao": study.version_display},
            new_value={"versao": copy.version_display},
            reason=reason,
        )
    return copy
