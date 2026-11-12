"""Execução das qualificações de instalação e de operação com relatório em PDF guardado
(FR-011 a FR-013 da feature 014). A execução é somente de inclusão e vai para a trilha."""

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from sgp.accounts.profiles import Profile, active_profiles
from sgp.audit.services import record_event
from sgp.files.storage import store_bytes

from . import installation, operation, version
from .checks import FAILED, NOT_APPLICABLE, RESULT_LABELS
from .models import QualificationChannel, QualificationKind, QualificationRun

ALLOWED = {
    QualificationKind.INSTALLATION: {Profile.ADMIN},
    QualificationKind.OPERATION: {Profile.ADMIN, Profile.QUALITY},
}
PREFIX = {QualificationKind.INSTALLATION: "IQ", QualificationKind.OPERATION: "OQ"}


def can_execute(user, kind: str) -> bool:
    return bool(ALLOWED[kind] & active_profiles(user))


def execute(kind: str, *, by, channel: str = QualificationChannel.SCREEN) -> QualificationRun:
    if kind not in ALLOWED:
        raise ValueError(f"Tipo de qualificação inexistente: {kind}")
    if not can_execute(by, kind):
        raise PermissionDenied(
            "Só a TI executa a qualificação de instalação; a de operação, a TI ou a Garantia da "
            "Qualidade."
        )
    started = timezone.now()
    items = installation.run() if kind == QualificationKind.INSTALLATION else operation.run()
    finished = timezone.now()
    passed = not any(item["resultado"] == FAILED for item in items)
    system_version = version.display()
    pdf = render_report(kind, by, channel, started, finished, items, passed, system_version)
    stamp = timezone.localtime(started).strftime("%Y%m%d-%H%M%S")
    stored = store_bytes(pdf, name=f"qualificacao-{PREFIX[kind]}-{stamp}.pdf", kind="pdf", by=by)
    with transaction.atomic():
        run = QualificationRun.objects.create(
            kind=kind,
            channel=channel,
            executed_by=by,
            started_at=started,
            finished_at=finished,
            system_version=system_version,
            items=items,
            passed=passed,
            report=stored,
        )
        record_event(
            "operations.qualification_executed",
            actor=by,
            obj=run,
            new_value={
                "tipo": kind,
                "canal": channel,
                "aprovada": passed,
                "reprovados": [i["codigo"] for i in items if i["resultado"] == FAILED],
                "nao_aplicaveis": [i["codigo"] for i in items if i["resultado"] == NOT_APPLICABLE],
                "versao": system_version,
                "relatorio_sha256": stored.sha256,
            },
        )
    return run


def render_report(kind, by, channel, started, finished, items, passed, system_version) -> bytes:
    import weasyprint

    rows = [
        {**item, "rotulo": RESULT_LABELS.get(item["resultado"], item["resultado"])}
        for item in items
    ]
    context = {
        "titulo": QualificationKind(kind).label,
        "prefixo": PREFIX[kind],
        "executor": by.get_full_name() or by.username,
        "login": by.username,
        "canal": QualificationChannel(channel).label,
        "inicio": timezone.localtime(started),
        "fim": timezone.localtime(finished),
        "versao": system_version,
        "endereco": settings.SITE_URL,
        "aprovada": passed,
        "itens": rows,
        "reprovados": sum(1 for i in items if i["resultado"] == FAILED),
        "nao_aplicaveis": sum(1 for i in items if i["resultado"] == NOT_APPLICABLE),
    }
    html = render_to_string("operations/report.html", context)
    return weasyprint.HTML(string=html).write_pdf(pdf_variant="pdf/a-2b")
