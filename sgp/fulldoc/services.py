"""Pedir, gerar, reaproveitar, baixar e verificar o documento completo (feature 009)."""

import hashlib
import logging

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from sgp.accounts.profiles import Profile, active_profiles
from sgp.audit.services import record_event
from sgp.core.access import can_access_project
from sgp.documents import render_pdf, seal
from sgp.documents.layouts import current_layout
from sgp.documents.models import LayoutTarget
from sgp.documents.services import verification_code
from sgp.files.storage import IntegrityFailure, read_verified, record_integrity_failure, store_bytes
from sgp.projects.permissions import can_view_financials

from . import compose, pending, versioning
from . import render as renderer
from .models import (
    NOTEBOOK_FULL,
    NOTEBOOK_SUMMARY,
    FullDocument,
    FullDocumentRequest,
    RequestStatus,
)

logger = logging.getLogger(__name__)
KIND = "project"
FRIENDLY_ERRORS = (seal.SealError, ValidationError, IntegrityFailure)


def can_generate(user, project) -> bool:
    """Líder do projeto e Gestor de P&D, com acesso ao projeto (FR-001)."""
    if not can_access_project(user, project):
        return False
    return project.leader_id == user.pk or Profile.RD_MANAGER in active_profiles(user)


def can_download(user, document: FullDocument) -> bool:
    if not can_access_project(user, document.project):
        return False
    return not document.with_financials or can_view_financials(user, document.project)


def _event(event_type: str, project, by, *, obj=None, **kwargs):
    return record_event(
        event_type,
        actor=by,
        obj=obj or project,
        project_id=project.pk,
        **kwargs,
    )


def normalize_options(data: dict) -> dict:
    notebook = data.get("caderno") or NOTEBOOK_SUMMARY
    if notebook not in (NOTEBOOK_SUMMARY, NOTEBOOK_FULL):
        raise ValidationError("Escolha o histórico do caderno completo ou resumido.")
    return {
        "caderno": notebook,
        "historico_versoes": bool(data.get("historico_versoes")),
        "omitir_financeiro": bool(data.get("omitir_financeiro")),
    }


def active_request(project) -> FullDocumentRequest | None:
    return (
        FullDocumentRequest.objects.filter(
            project=project, status__in=[RequestStatus.QUEUED, RequestStatus.RUNNING]
        )
        .order_by("-requested_at")
        .first()
    )


def request_document(project, *, by, options: dict, request=None) -> FullDocumentRequest:
    if not can_generate(by, project):
        raise PermissionDenied(
            "Só o líder do projeto e o Gestor de P&D geram o documento completo."
        )
    options = normalize_options(options)
    try:
        with transaction.atomic():
            pending_request = FullDocumentRequest.objects.create(
                project=project,
                project_version=project.version or 0,
                options=options,
                with_financials=can_view_financials(by, project)
                and not options["omitir_financeiro"],
                requested_by=by,
            )
            _event(
                "fulldoc.requested",
                project,
                by,
                new_value={"pedido": pending_request.pk, **options},
                request=request,
            )
    except IntegrityError as exc:
        raise ValidationError(
            "Já existe um documento completo sendo gerado para este projeto; aguarde terminar."
        ) from exc
    from .tasks import generate as generate_task

    transaction.on_commit(lambda: generate_task.delay(pending_request.pk))
    return pending_request


def _progress(pending_request, value: int, step: str) -> None:
    FullDocumentRequest.objects.filter(pk=pending_request.pk).update(progress=value, step=step)


def generate(pending_request: FullDocumentRequest) -> tuple[FullDocument, bool]:
    project = pending_request.project
    if (project.version or 0) != pending_request.project_version:
        raise ValidationError("O projeto mudou de versão depois do pedido; peça de novo.")
    layout = current_layout(LayoutTarget.SUBDOCUMENT)
    if layout is None:
        raise ValidationError("Não há modelo de layout de subdocumento vigente; avise a Qualidade.")
    _progress(pending_request, 5, "Conferindo pendências")
    items = pending.pending_items(project)
    official = not items
    _progress(pending_request, 15, "Montando as partes")
    final_version = versioning.ensure_current(project, by=pending_request.requested_by)
    now = timezone.now()
    composition = compose.compose(
        project,
        options=pending_request.options,
        with_financials=pending_request.with_financials,
        pending=items,
        until=now,
        final=final_version,
    )
    digest = compose.composition_digest(project, composition, layout_id=layout.pk, pending=items)
    final_number = final_version.number if final_version else 0
    existing = (
        FullDocument.objects.filter(project=project, composition_hash=digest, official=official)
        .order_by("generated_at", "pk")
        .first()
    )
    if existing is not None:
        return existing, True
    _progress(pending_request, 30, "Renderizando o PDF")
    code = verification_code(KIND, project.pk, final_number, digest, layout.pk) if official else ""
    local = timezone.localtime(now)
    by_name = pending_request.requested_by.get_full_name() or pending_request.requested_by.username
    pdf, pages = renderer.render(
        project,
        composition,
        layout,
        draft=not official,
        created=now.isoformat(),
        generated_label=local.strftime("%d/%m/%Y às %H:%M") + f" por {by_name}",
        identifier=render_pdf.identifier_for(
            KIND, project.pk, project.version or 0, digest, layout.pk
        ),
        verification_code=code,
        final_version=final_version,
    )
    content_digest = hashlib.sha256(pdf).hexdigest()
    _progress(pending_request, 80, "Aplicando o selo" if official else "Arquivando")
    final = seal.seal(pdf) if official else pdf
    name = f"Documento completo {project.code or project.pk} v{final_number:02d}.pdf"
    with transaction.atomic():
        stored = store_bytes(final, name=name, kind="pdf", by=pending_request.requested_by)
        document = FullDocument.objects.create(
            project=project,
            project_version=project.version or 0,
            options=pending_request.options,
            with_financials=pending_request.with_financials,
            official=official,
            pending=items,
            composition_hash=digest,
            layout=layout,
            file=stored,
            content_hash=content_digest,
            file_hash=stored.sha256,
            verification_code=code,
            pages=pages,
            generated_by=pending_request.requested_by,
            final_version=final_version,
        )
        _event(
            "fulldoc.generated",
            project,
            pending_request.requested_by,
            obj=document,
            new_value={
                "pedido": pending_request.pk,
                "oficial": official,
                "paginas": pages,
                "pendencias": len(items),
                "sha256": stored.sha256,
                "codigo": code,
                "dados_financeiros": pending_request.with_financials,
                "versao_documento_final": final_number or None,
                **pending_request.options,
            },
        )
    return document, False


def _friendly(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        return "; ".join(exc.messages)
    if isinstance(exc, IntegrityFailure):
        return "Um arquivo usado no documento (logotipo ou imagem do caderno) falhou na conferência de integridade."
    if isinstance(exc, FRIENDLY_ERRORS):
        return str(exc)
    return "Falha inesperada na geração; a TI foi avisada pela trilha de auditoria."


def run_request(request_id: int) -> FullDocumentRequest:
    """Executa o pedido (worker). Nunca levanta: falha vira situação "Falhou" com alerta."""
    with transaction.atomic():
        pending_request = FullDocumentRequest.objects.select_for_update().get(pk=request_id)
        if pending_request.status != RequestStatus.QUEUED:
            return pending_request
        pending_request.status = RequestStatus.RUNNING
        pending_request.started_at = timezone.now()
        pending_request.save(update_fields=["status", "started_at"])
    try:
        document, reused = generate(pending_request)
    except Exception as exc:  # noqa: BLE001 - toda falha fica registrada e visível
        if not isinstance(exc, FRIENDLY_ERRORS):
            logger.exception("Falha na geração do documento completo %s", request_id)
        if isinstance(exc, IntegrityFailure):
            record_integrity_failure(exc)
        message = _friendly(exc)
        with transaction.atomic():
            FullDocumentRequest.objects.filter(pk=request_id).update(
                status=RequestStatus.FAILED, error=message, finished_at=timezone.now()
            )
            _event(
                "fulldoc.failed",
                pending_request.project,
                pending_request.requested_by,
                new_value={"pedido": request_id, "erro": message},
            )
    else:
        with transaction.atomic():
            FullDocumentRequest.objects.filter(pk=request_id).update(
                status=RequestStatus.DONE,
                result=document,
                reused=reused,
                progress=100,
                step="Concluído",
                finished_at=timezone.now(),
            )
            if reused:
                _event(
                    "fulldoc.reused",
                    pending_request.project,
                    pending_request.requested_by,
                    obj=document,
                    new_value={"pedido": request_id, "documento": document.pk},
                )
    pending_request.refresh_from_db()
    return pending_request


def history(project):
    return FullDocument.objects.filter(project=project).select_related("generated_by")


def download(document: FullDocument, *, by, request=None) -> bytes:
    if not can_download(by, document):
        raise PermissionDenied(
            "O documento contém dados financeiros do Plano de Negócios; só quem tem essa "
            "permissão o baixa."
            if can_access_project(by, document.project)
            else "Sem acesso ao projeto do documento."
        )
    data = read_verified(document.file)
    _event(
        "fulldoc.downloaded",
        document.project,
        by,
        obj=document,
        new_value={"documento": document.pk, "sha256": document.file_hash},
        request=request,
    )
    return data


def _version_label(document) -> str:
    """Versão mostrada na verificação: a do documento final (016) e a do projeto."""
    if document.final_version_id:
        return (
            f"{document.final_version.number:02d} do documento final "
            f"(projeto {document.project_version:02d})"
        )
    return f"{document.project_version:02d}"


def lookup_code(code: str, user) -> dict | None:
    """Consulta extra da tela de verificação da 006 (research R11)."""
    documents = list(
        FullDocument.objects.filter(verification_code=code, official=True)
        .select_related("project", "final_version")
        .order_by("generated_at", "pk")
    )
    if not documents:
        return None
    first = documents[0]
    project = first.project
    access = can_access_project(user, project)
    return {
        "kind_label": "Documento completo do projeto",
        "title": f"{project.code or ''} {project.title}".strip(),
        "version": _version_label(first),
        "situation": f"{first.pages} página(s); gerado em "
        + timezone.localtime(first.generated_at).strftime("%d/%m/%Y %H:%M"),
        "approved_on": "todas as partes aprovadas na geração",
        "signatures": [],
        "files": documents,
        "access": access,
        "project": project if access else None,
        "project_id": project.pk if access else None,
        "fulldoc": True,
    }
