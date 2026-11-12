"""Promoção de um anexo CSV/XLSX da entrada para um estudo da feature 007 (FR-011; research R9).

Os bytes são lidos com conferência do resumo e passam pela importação da 007 (pré-visualização
assinada e confirmação); o vínculo de promoção nasce na mesma transação da confirmação.
"""

from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.db import transaction

from sgp.files.storage import read_verified
from sgp.studies import importing
from sgp.studies import services as study_services
from sgp.studies.models import Study, StudyStatus

from . import permissions
from .models import EntryAttachment, LinkKind, LinkTarget, NotebookLink
from .services import _event

SALT = "sgp.notebook.promotion"
MAX_AGE = 60 * 60


def spreadsheets(entry):
    return [
        item
        for item in entry.attachments.filter(removed_at__isnull=True).select_related("file")
        if item.is_spreadsheet
    ]


def target_studies(entry) -> list[Study]:
    """Versão mais recente de cada estudo do projeto que ainda aceita linhas."""
    latest = {}
    for study in (
        Study.objects.filter(project=entry.project)
        .select_related("study_type")
        .order_by("lineage", "-version")
    ):
        latest.setdefault(study.lineage, study)
    return sorted(
        (
            study
            for study in latest.values()
            if study.status == StudyStatus.EDITING and not study.not_applicable
        ),
        key=lambda study: study.title,
    )


def _check(entry, attachment: EntryAttachment, study: Study, by) -> None:
    if not permissions.can_link(by, entry) or not study_services.can_edit(by, entry.project):
        raise PermissionDenied("Só os editores do projeto promovem dados para estudos.")
    if attachment.entry_id != entry.pk or attachment.removed_at or not attachment.is_spreadsheet:
        raise ValidationError("Escolha um anexo CSV ou XLSX ativo desta entrada.")
    if study.project_id != entry.project_id:
        raise ValidationError("Só estudos do mesmo projeto recebem dados da entrada.")
    if study.status != StudyStatus.EDITING or study.not_applicable:
        raise ValidationError("O estudo precisa estar em elaboração e com medidas (não aplicável recusado).")


def preview(entry, *, by, attachment: EntryAttachment, study: Study, mapping: dict) -> dict:
    _check(entry, attachment, study, by)
    data = read_verified(attachment.file)
    result = importing.preview(
        study, ContentFile(data, name=attachment.file.original_name), mapping
    )
    result["token"] = signing.dumps(
        {
            "entry": entry.pk,
            "attachment": attachment.pk,
            "study": study.pk,
            "inner": result["token"],
        },
        salt=SALT,
    )
    return result


def confirm(entry, *, by, token: str, equipment: str, mapping: dict) -> NotebookLink:
    try:
        payload = signing.loads(token, salt=SALT, max_age=MAX_AGE)
    except signing.BadSignature as exc:
        raise ValidationError("A pré-visualização expirou; faça a promoção de novo.") from exc
    if payload["entry"] != entry.pk:
        raise ValidationError("A pré-visualização é de outra entrada.")
    attachment = EntryAttachment.objects.select_related("file").get(pk=payload["attachment"])
    study = Study.objects.get(pk=payload["study"])
    _check(entry, attachment, study, by)
    origin = {
        "entrada": entry.pk,
        "numero_entrada": entry.number,
        "anexo": attachment.file_id,
        "nome": attachment.file.original_name,
        "sha256": attachment.file.sha256,
    }
    with transaction.atomic():
        count = importing.confirm(
            study,
            by=by,
            token=payload["inner"],
            equipment=equipment,
            mapping=mapping,
            origin=origin,
        )
        created = NotebookLink.objects.create(
            entry=entry,
            target_type=LinkTarget.STUDY,
            study=study,
            kind=LinkKind.PROMOTED,
            attachment=attachment,
            created_by=by,
        )
        _event(
            "notebook.promoted",
            entry,
            by,
            new_value={
                "estudo": study.pk,
                "titulo_estudo": study.title,
                "versao_estudo": study.version,
                "linhas": count,
                **origin,
            },
        )
    return created
