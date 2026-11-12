"""Regras do dossiê técnico (feature 011): definição, textos, empresa, complementos, geração,
envio, resultado e aditamento. Toda alteração registra o evento na mesma transação."""

import io
import zipfile

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from sgp.accounts.profiles import Profile, active_profiles
from sgp.audit.services import record_event
from sgp.core.access import can_access_project
from sgp.documents.render_pdf import identifier_for
from sgp.files.storage import read_verified, store_bytes, store_upload
from sgp.signatures.canonical import content_hash
from sgp.signatures.reauth import reauthenticate

from . import check, definition, diff, render
from .models import (
    CompanyProfile,
    DossierDefinition,
    DossierSupplement,
    DossierVersion,
    StandardText,
    Submission,
    SubmissionResult,
    TextStatus,
)

QUALITY_ONLY = "Só a Qualidade/Assuntos Regulatórios mantém o dossiê técnico."


def is_quality(user) -> bool:
    return Profile.QUALITY in active_profiles(user)


def is_manager(user) -> bool:
    return Profile.RD_MANAGER in active_profiles(user)


def _require_quality(user) -> None:
    if not is_quality(user):
        raise PermissionDenied(QUALITY_ONLY)


def can_view(user, project) -> bool:
    return can_access_project(user, project)


# ------------------------------------------------------------------ definição


def current_definition() -> DossierDefinition:
    current = DossierDefinition.objects.order_by("-version").first()
    if current is None:
        raise ValidationError("Não há definição do dossiê publicada.")
    return current


def publish_definition(*, by, text: str, note: str = "") -> DossierDefinition:
    _require_quality(by)
    parsed = definition.parse(text)
    with transaction.atomic():
        number = (DossierDefinition.objects.aggregate(top=Max("version"))["top"] or 0) + 1
        record = DossierDefinition.objects.create(
            version=number, yaml=text, parsed=parsed, note=note[:500], created_by=by
        )
        record_event(
            "dossier.definition_published",
            actor=by,
            obj=record,
            new_value={"versao": number, "itens": len(list(definition.leaves(parsed["itens"])))},
            reason=note[:500],
        )
    return record


# ------------------------------------------------------------------ textos padrão


def save_text(*, by, key: str, title: str, text: str) -> StandardText:
    _require_quality(by)
    key, title, text = (key or "").strip(), (title or "").strip(), (text or "").strip()
    if not key or not title or not text:
        raise ValidationError("Informe chave, título e texto.")
    with transaction.atomic():
        number = (
            StandardText.objects.filter(key=key).aggregate(top=Max("version"))["top"] or 0
        ) + 1
        record = StandardText.objects.create(
            key=key, version=number, title=title[:200], text=text, created_by=by
        )
        record_event(
            "dossier.text_saved",
            actor=by,
            obj=record,
            new_value={"chave": key, "versao": number, "texto": text},
        )
    return record


def approve_text(record: StandardText, *, by, password: str, request=None) -> StandardText:
    profiles = active_profiles(by)
    if not (profiles & {Profile.QUALITY, Profile.RD_MANAGER}):
        raise PermissionDenied("Só a Qualidade/AR ou o Gestor de P&D aprova textos padrão.")
    if record.created_by_id == by.pk:
        raise ValidationError("Quem escreveu o texto não pode aprová-lo.")
    if record.status != TextStatus.DRAFT:
        raise ValidationError("Só textos em elaboração são aprovados.")
    reauthenticate(request, by, password)
    with transaction.atomic():
        StandardText.objects.filter(key=record.key, status=TextStatus.APPROVED).update(
            status=TextStatus.SUPERSEDED
        )
        record.status = TextStatus.APPROVED
        record.approved_by = by
        record.approved_at = timezone.now()
        record.save(update_fields=["status", "approved_by", "approved_at"])
        record_event(
            "dossier.text_approved",
            actor=by,
            obj=record,
            new_value={"chave": record.key, "versao": record.version},
            request=request,
        )
    return record


# ------------------------------------------------------------------ empresa e complementos


def company() -> CompanyProfile | None:
    return CompanyProfile.objects.order_by("-pk").first()


COMPANY_FIELDS = ("legal_name", "city", "rt_name", "rt_council", "rt_uf", "rt_number", "rt_title")


def save_company(*, by, data: dict) -> CompanyProfile:
    _require_quality(by)
    values = {name: (data.get(name) or "").strip() for name in COMPANY_FIELDS}
    required = ("legal_name", "city", "rt_name", "rt_council", "rt_uf", "rt_number")
    if any(not values[name] for name in required):
        raise ValidationError(
            "Preencha razão social, cidade e os dados do responsável técnico e legal."
        )
    values["rt_uf"] = values["rt_uf"].upper()[:2]
    with transaction.atomic():
        current = company()
        before = {name: getattr(current, name) for name in COMPANY_FIELDS} if current else None
        if current is None:
            current = CompanyProfile.objects.create(updated_by=by, **values)
        else:
            for name, value in values.items():
                setattr(current, name, value)
            current.updated_by = by
            current.updated_at = timezone.now()
            current.save()
        record_event(
            "dossier.company_updated", actor=by, obj=current, old_value=before, new_value=values
        )
    return current


def save_supplement(
    project, *, by, item_key: str, text: str, not_applicable: bool, justification: str
):
    _require_quality(by)
    if not can_access_project(by, project):
        raise PermissionDenied("Sem acesso ao projeto.")
    keys = {item["key"] for item, _ in definition.leaves(current_definition().parsed["itens"])}
    if item_key not in keys:
        raise ValidationError("Item do dossiê inexistente.")
    text, justification = (text or "").strip(), (justification or "").strip()
    if not_applicable and not justification:
        raise ValidationError("Informe a justificativa do não aplicável.")
    if not not_applicable and not text:
        raise ValidationError("Escreva o texto do item ou marque como não aplicável.")
    with transaction.atomic():
        record = DossierSupplement.objects.filter(project=project, item_key=item_key).first()
        before = (
            {
                "texto": record.text,
                "nao_aplicavel": record.not_applicable,
                "justificativa": record.justification,
            }
            if record
            else None
        )
        if record is None:
            record = DossierSupplement(project=project, item_key=item_key, updated_by=by)
        record.text, record.not_applicable, record.justification = (
            text,
            bool(not_applicable),
            justification,
        )
        record.updated_by, record.updated_at = by, timezone.now()
        record.save()
        record_event(
            "dossier.supplement_saved",
            actor=by,
            obj=record,
            project_id=project.pk,
            old_value=before,
            new_value={
                "item": item_key,
                "texto": text,
                "nao_aplicavel": bool(not_applicable),
                "justificativa": justification,
            },
        )
    return record


# ------------------------------------------------------------------ checagem e geração


def checklist(project) -> dict:
    current = current_definition()
    result = check.evaluate(project, current.parsed)
    result["definition"] = current
    result["company"] = company()
    for item in result["items"]:
        item["path_label"] = " › ".join(f"{p['numero']}. {p['titulo']}" for p in item["path"])
    result["missing"] = [item for item in result["items"] if item["status"] == "missing"]
    if result["company"] is None:
        result["company_missing"] = True
    result["final_allowed"] = not result["missing"] and result["company"] is not None
    return result


def _package(name: str, pdf_bytes: bytes, docx_bytes: bytes, annexes: list) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(zipfile.ZipInfo(f"{name}.pdf", date_time=(1980, 1, 1, 0, 0, 0)), pdf_bytes)
        archive.writestr(
            zipfile.ZipInfo(f"{name}.docx", date_time=(1980, 1, 1, 0, 0, 0)), docx_bytes
        )
        for ref in annexes:
            data = read_verified(ref["file"])
            info = zipfile.ZipInfo(
                f"anexos/Anexo {ref['number']:02d} - {ref['file'].original_name}",
                date_time=(1980, 1, 1, 0, 0, 0),
            )
            archive.writestr(info, data)
    return buffer.getvalue()


def generate(project, *, by) -> DossierVersion:
    _require_quality(by)
    if not can_access_project(by, project):
        raise PermissionDenied("Sem acesso ao projeto.")
    result = checklist(project)
    final = result["final_allowed"]
    tree = render.build_tree(result["definition"].parsed, result)
    content = render.canonical(tree)
    subject = check.subject(project)
    product = project.product_name
    day = timezone.localdate()
    texts_used = {
        used["chave"]: used["versao"]
        for item in result["items"]
        for used in item.get("used", [])
        if used.get("tipo") == "texto_padrao"
    }
    sources_used = {item["key"]: item.get("used", []) for item in result["items"]}
    digest = content_hash({"conteudo": content, "final": final, "classe": result["risk_class"]})
    with transaction.atomic():
        number = (
            DossierVersion.objects.filter(subject=subject).aggregate(top=Max("number"))["top"] or 0
        ) + 1
        identifier = identifier_for("dossie", subject, number, digest)
        pdf_bytes = render.pdf(
            tree=tree,
            product=product,
            company=result["company"],
            draft=not final,
            missing=result["missing"],
            day=day,
            identifier=identifier,
        )
        docx_bytes = render.docx(
            tree=tree,
            product=product,
            company=result["company"],
            draft=not final,
            missing=result["missing"],
            day=day,
        )
        name = f"Dossie Tecnico {subject} v{number:02d}" + ("" if final else " RASCUNHO")
        pdf_file = store_bytes(pdf_bytes, name=f"{name}.pdf", kind="pdf", by=by)
        docx_file = store_bytes(docx_bytes, name=f"{name}.docx", kind="docx", by=by)
        package = None
        if final:
            package = store_bytes(
                _package(name, pdf_bytes, docx_bytes, tree["annexes"]),
                name=f"{name}.zip",
                kind="zip",
                by=by,
            )
        version = DossierVersion.objects.create(
            subject=subject,
            project=project,
            number=number,
            definition=result["definition"],
            risk_class=result["risk_class"] or "",
            final=final,
            checklist=[
                {
                    "item": item["key"],
                    "titulo": item["path_label"],
                    "situacao": item["status"],
                    "origem": item["origin"],
                    "motivo": item.get("reason", ""),
                    "justificativa": item.get("justification", ""),
                }
                for item in result["items"]
            ],
            content=content,
            content_hash=digest,
            texts_used=texts_used,
            sources=sources_used,
            pdf=pdf_file,
            docx=docx_file,
            package=package,
            generated_by=by,
        )
        record_event(
            "dossier.generated",
            actor=by,
            obj=version,
            project_id=project.pk,
            new_value={
                "versao": number,
                "final": final,
                "classe": result["risk_class"],
                "faltando": len(result["missing"]),
                "anexos": len(tree["annexes"]),
                "pdf_sha256": pdf_file.sha256,
                "definicao": result["definition"].version,
            },
        )
    return version


def versions(project):
    return DossierVersion.objects.filter(subject=check.subject(project)).select_related(
        "pdf", "docx", "package", "generated_by"
    )


def download(version: DossierVersion, kind: str, *, by, request=None):
    if not can_access_project(by, version.project):
        raise PermissionDenied("Sem acesso ao projeto do dossiê.")
    stored = {"pdf": version.pdf, "docx": version.docx, "pacote": version.package}.get(kind)
    if stored is None:
        raise ValidationError("Arquivo inexistente para esta versão.")
    data = read_verified(stored)
    record_event(
        "dossier.downloaded",
        actor=by,
        obj=version,
        project_id=version.project_id,
        new_value={"arquivo": kind, "sha256": stored.sha256},
        request=request,
    )
    return stored, data


# ------------------------------------------------------------------ envio, resultado e aditamento


def submit(
    version: DossierVersion, *, by, protocol: str, submitted_on, signed_pdf=None
) -> Submission:
    _require_quality(by)
    if not version.final:
        raise ValidationError("Só o dossiê final é enviado; resolva as pendências e gere de novo.")
    if version.risk_class == "I":
        raise ValidationError("Classe I: o dossiê fica arquivado para inspeção, sem envio.")
    protocol = (protocol or "").strip()
    if not protocol or not submitted_on:
        raise ValidationError("Informe o número do processo ou expediente e a data do envio.")
    with transaction.atomic():
        signed = store_upload(signed_pdf, by=by, allowed=("pdf",)) if signed_pdf else None
        record = Submission.objects.create(
            version=version,
            protocol=protocol[:80],
            submitted_on=submitted_on,
            signed_pdf=signed,
            created_by=by,
            updated_by=by,
        )
        record_event(
            "dossier.submitted",
            actor=by,
            obj=record,
            project_id=version.project_id,
            new_value={
                "versao": version.number,
                "protocolo": record.protocol,
                "data": submitted_on,
                "pdf_assinado": signed.sha256 if signed else None,
            },
        )
    return record


def record_result(
    submission: Submission, *, by, result: str, result_on, notes: str = ""
) -> Submission:
    _require_quality(by)
    if result not in SubmissionResult.values or result == SubmissionResult.PENDING:
        raise ValidationError("Escolha deferido, indeferido ou exigência.")
    if not result_on:
        raise ValidationError("Informe a data do resultado.")
    with transaction.atomic():
        before = {"resultado": submission.result, "data": submission.result_on}
        submission.result, submission.result_on = result, result_on
        submission.notes = (notes or "").strip()
        submission.updated_by, submission.updated_at = by, timezone.now()
        submission.save()
        record_event(
            "dossier.result_recorded",
            actor=by,
            obj=submission,
            project_id=submission.version.project_id,
            old_value=before,
            new_value={"resultado": result, "data": result_on, "observacoes": submission.notes},
        )
    return submission


def last_submitted(version: DossierVersion) -> DossierVersion | None:
    submission = (
        Submission.objects.filter(
            version__subject=version.subject, version__number__lt=version.number
        )
        .select_related("version")
        .order_by("-version__number", "-submitted_on")
        .first()
    )
    return submission.version if submission else None


def addendum(version: DossierVersion, *, by, request=None, as_pdf: bool = False):
    if not can_access_project(by, version.project):
        raise PermissionDenied("Sem acesso ao projeto do dossiê.")
    previous = last_submitted(version)
    if previous is None:
        return None, [], None
    changes = diff.changes(previous.content, version.content)
    data = None
    if as_pdf:
        data = render.addendum_pdf(
            product=version.project.product_name,
            version=version,
            previous=previous,
            changes=changes,
            identifier=identifier_for("aditamento", version.pk, previous.pk),
        )
        record_event(
            "dossier.addendum_generated",
            actor=by,
            obj=version,
            project_id=version.project_id,
            new_value={
                "versao": version.number,
                "versao_enviada": previous.number,
                "itens_alterados": [c["key"] for c in changes],
            },
            request=request,
        )
    return previous, changes, data
