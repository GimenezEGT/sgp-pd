"""Itens da qualificação de operação (FR-012 da feature 014, research R8).

Nenhum dado é alterado: as tentativas de alteração rodam como o papel da aplicação dentro de um
ponto de salvamento desfeito, e as contagens do banco são comparadas antes e depois.
"""

import io
from datetime import timedelta

from django.conf import settings
from django.db import DatabaseError, connection, transaction
from django.utils import timezone
from psycopg import sql

from sgp.audit.models import AuditEvent
from sgp.audit.services import walk_chain

from . import backup, restore
from .checks import APPROVED, FAILED, NOT_APPLICABLE, Item, run_items, worker_ping
from .installation import REQUIRED_JOBS

TEST_HTML = (
    "<html><head><meta charset='utf-8'><title>Qualificação de operação</title></head>"
    "<body><h1>SGP-P&amp;D — documento de teste da qualificação de operação</h1>"
    "<p>Conteúdo fictício gerado em memória; não é guardado.</p></body></html>"
)


class _Accepted(Exception):
    """A alteração foi aceita (e é desfeita): a conferência reprova."""


def _attempt(statement: str) -> tuple[bool, str]:
    """Executa a alteração como o papel da aplicação; True se o banco a recusou."""
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(settings.DB_APP_ROLE))
                )
                cursor.execute(statement)
            raise _Accepted
    except _Accepted:
        return False, "Alteração aceita pelo banco (desfeita)."
    except DatabaseError as exc:
        reason = str(exc).strip().splitlines()[0][:160]
        return True, f"Recusada pelo banco: {reason}"


def _table_has_rows(table: str) -> bool:
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT EXISTS (SELECT 1 FROM "{table}")')  # noqa: S608 - nome do modelo
        return cursor.fetchone()[0]


def _chain():
    count, breaks, head_seq, _head = walk_chain(AuditEvent.objects.all())
    if breaks:
        return FAILED, f"{len(breaks)} quebra(s) em {count} eventos."
    return APPROVED, f"{count} eventos íntegros; último {head_seq}."


def _refuse(table: str, statement: str):
    if not _table_has_rows(table):
        return NOT_APPLICABLE, f"Tabela {table} sem registros."
    refused, detail = _attempt(statement)
    return (APPROVED if refused else FAILED), detail


def _audit_update():
    table = AuditEvent._meta.db_table
    return _refuse(
        table,
        f'UPDATE "{table}" SET reason = reason WHERE seq = (SELECT max(seq) FROM "{table}")',  # noqa: S608
    )


def _audit_delete():
    table = AuditEvent._meta.db_table
    return _refuse(
        table,
        f'DELETE FROM "{table}" WHERE seq = (SELECT max(seq) FROM "{table}")',  # noqa: S608
    )


def _signed_version_update():
    from sgp.signatures.models import ApprovedVersion

    table = ApprovedVersion._meta.db_table
    return _refuse(
        table,
        f'UPDATE "{table}" SET content_hash = content_hash '  # noqa: S608
        f'WHERE id = (SELECT min(id) FROM "{table}")',
    )


def _protected_delete():
    from sgp.projects.models import Project

    table = Project._meta.db_table
    return _refuse(
        table,
        f'DELETE FROM "{table}" WHERE id = (SELECT min(id) FROM "{table}")',  # noqa: S608
    )


def _pdf_and_seal():
    import weasyprint
    from pypdf import PdfReader

    from sgp.documents import seal

    data = weasyprint.HTML(string=TEST_HTML).write_pdf(pdf_variant="pdf/a-2b")
    pages = len(PdfReader(io.BytesIO(data)).pages)
    try:
        sealed = seal.seal(data)
        signer = seal.load_signer()
    except seal.SealError as exc:
        return FAILED, f"PDF de teste gerado ({pages} página), mas o selo falhou: {exc}"
    status = seal.validate(sealed, [signer.signing_cert])
    if not (status["intact"] and status["valid"]):
        return FAILED, "Selo aplicado, mas a validação não confirmou a integridade."
    return APPROVED, f"PDF/A de teste gerado ({pages} página) e selado; selo íntegro e válido."


def _schedules():
    missing = [job for job in REQUIRED_JOBS if job not in settings.CELERY_BEAT_SCHEDULE]
    if missing:
        return FAILED, "Agendamentos ausentes: " + ", ".join(missing) + "."
    workers = worker_ping()
    if not workers:
        return FAILED, "Nenhum worker respondeu; as tarefas agendadas não rodam."
    return (
        APPROVED,
        f"Worker(s) {', '.join(workers)} com {len(REQUIRED_JOBS)} agendamentos de operação.",
    )


def _backup_fresh():
    latest = backup.latest_success()
    limit = timezone.now() - timedelta(hours=settings.BACKUP_MAX_AGE_HOURS)
    if latest is None or not latest.finished_at:
        return FAILED, "Nenhuma cópia de segurança bem-sucedida."
    when = timezone.localtime(latest.finished_at)
    if latest.finished_at < limit:
        return (
            FAILED,
            f"Última cópia em {when:%d/%m/%Y %H:%M} (mais de {settings.BACKUP_MAX_AGE_HOURS} horas).",
        )
    return APPROVED, f"Última cópia {latest.label} em {when:%d/%m/%Y %H:%M}."


def _restore_fresh():
    latest = restore.latest_test()
    limit = timezone.now() - timedelta(days=settings.RESTORE_TEST_MAX_AGE_DAYS)
    if latest is None:
        return FAILED, "Nenhum teste de restauração executado."
    when = timezone.localtime(latest.started_at)
    if latest.status != "passed":
        return FAILED, f"Último teste ({when:%d/%m/%Y}) reprovado: {latest.error[:120]}"
    if latest.started_at < limit:
        return (
            FAILED,
            f"Último teste aprovado em {when:%d/%m/%Y} (mais de {settings.RESTORE_TEST_MAX_AGE_DAYS} dias).",
        )
    return APPROVED, f"Último teste aprovado em {when:%d/%m/%Y %H:%M}."


def _sankhya():
    from sgp.integrations import sankhya

    if not sankhya.configured():
        return NOT_APPLICABLE, "Integração com o Sankhya desligada (contingência em arquivo)."
    sankhya.token(force=True)
    return APPROVED, "Autenticação no API Gateway da Sankhya aceita."


ITEMS: list[Item] = [
    ("OQ-01", "Cadeia da trilha de auditoria íntegra", _chain),
    ("OQ-02", "Alteração de evento da trilha recusada pelo banco", _audit_update),
    ("OQ-03", "Exclusão de evento da trilha recusada pelo banco", _audit_delete),
    ("OQ-04", "Alteração de versão assinada recusada pelo banco", _signed_version_update),
    ("OQ-05", "Exclusão de registro protegido recusada pelo banco", _protected_delete),
    ("OQ-06", "PDF de teste gerado e selado, com selo íntegro", _pdf_and_seal),
    ("OQ-07", "Agendamentos de operação ativos", _schedules),
    ("OQ-08", "Cópia de segurança em dia", _backup_fresh),
    ("OQ-09", "Teste de restauração aprovado em dia", _restore_fresh),
    ("OQ-10", "Integração com o Sankhya", _sankhya),
]


def _counts() -> dict:
    with connection.cursor() as cursor:
        return backup.table_counts(cursor)


def run() -> list[dict]:
    before = _counts()
    results = run_items(ITEMS)
    after = _counts()
    changed = sorted(t for t in set(before) | set(after) if before.get(t) != after.get(t))
    results.append(
        {
            "codigo": "OQ-11",
            "descricao": "Nenhum dado alterado pela qualificação",
            "resultado": FAILED if changed else APPROVED,
            "detalhe": ("Contagens alteradas em: " + ", ".join(changed[:10]))
            if changed
            else f"Contagens de {len(after)} tabelas iguais antes e depois.",
        }
    )
    return results
