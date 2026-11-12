"""Teste de restauração: a cópia mais recente é restaurada num banco isolado e descartável e
conferida item a item (C1 a C6, research R5 e contrato copia-e-manifesto.md da feature 014).

O banco em uso nunca é tocado: só o banco `<NAME>_restauracao` é criado e descartado.
"""

import json
import logging
import subprocess
from datetime import timedelta

from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone
from psycopg import sql

from sgp.audit.chain import HASH_FIELDS
from sgp.audit.models import AuditEvent
from sgp.audit.services import record_event, walk_rows

from . import alerts
from .backup import (
    MANIFEST,
    AdvisoryLock,
    BackupBusy,
    copies_dir,
    latest_success,
    owner_connect,
    owner_params,
    pg_env,
    pool_path,
    sha256_file,
    table_counts,
)
from .models import BackupRun, BackupStatus, RestoreStatus, RestoreTest, RunKind

logger = logging.getLogger(__name__)

RESTORE_LOCK = 0x53475002
RESTORE_TIMEOUT = 6 * 3600
DESCRIPTIONS = {
    "C1": "Resumo do manifesto igual ao registrado na cópia",
    "C2": "Resumo do banco copiado igual ao do manifesto",
    "C3": "Restauração no banco isolado sem erro",
    "C4": "Contagem de linhas de cada tabela igual à do manifesto",
    "C5": "Cadeia da trilha íntegra até o último evento do manifesto",
    "C6": "Arquivos do manifesto presentes no acervo com o resumo conferido",
}


class RestoreBusy(BackupBusy):
    """Já há um teste de restauração em andamento."""


class _Stop(Exception):
    """Conferência reprovada que impede as seguintes."""


def restore_db_name() -> str:
    return f"{connection.settings_dict['NAME']}_restauracao"[:63]


def run_restore_test(
    *, kind: str = RunKind.SCHEDULED, by=None, backup: BackupRun | None = None
) -> RestoreTest:
    with AdvisoryLock(RESTORE_LOCK, "Já há um teste de restauração em andamento.", RestoreBusy):
        backup = backup or latest_success()
        test = RestoreTest.objects.create(backup=backup, kind=kind, requested_by=by)
        checks: list[dict] = []
        error = ""
        try:
            if backup is None:
                raise _Stop("Não há cópia de segurança bem-sucedida para testar.")
            _run_checks(backup, checks)
        except _Stop as exc:
            error = str(exc)
        except Exception as exc:  # noqa: BLE001 - toda falha vira reprovação registrada
            logger.exception("Falha inesperada no teste de restauração %s", test.pk)
            error = f"Erro inesperado: {exc.__class__.__name__}: {exc}"
        finally:
            _drop_database()
        passed = (
            not error and len(checks) == len(DESCRIPTIONS) and all(c["aprovado"] for c in checks)
        )
        if not passed and not error:
            error = "; ".join(f"{c['codigo']}: {c['detalhe']}" for c in checks if not c["aprovado"])
        return _finish(test, checks, passed, error)


def _check(checks: list, code: str, ok: bool, detail: str, *, stop: bool = True) -> None:
    checks.append(
        {"codigo": code, "descricao": DESCRIPTIONS[code], "aprovado": bool(ok), "detalhe": detail}
    )
    if not ok and stop:
        raise _Stop(f"{code}: {detail}")


def _run_checks(backup: BackupRun, checks: list) -> None:
    folder = copies_dir() / backup.label
    manifest_path = folder / MANIFEST
    if not manifest_path.is_file():
        _check(checks, "C1", False, f"Manifesto ausente em {folder}.")
    actual = sha256_file(manifest_path)
    _check(
        checks,
        "C1",
        actual == backup.manifest_sha256,
        "Resumo conferido."
        if actual == backup.manifest_sha256
        else f"Resumo {actual[:12]} difere do registrado {backup.manifest_sha256[:12]}.",
    )
    manifest = json.loads(manifest_path.read_bytes().decode("utf-8"))
    dump = folder / manifest["banco"]["arquivo"]
    expected = manifest["banco"]["sha256"]
    dump_sha = sha256_file(dump) if dump.is_file() else ""
    _check(
        checks,
        "C2",
        dump_sha == expected,
        "Resumo conferido."
        if dump_sha == expected
        else ("Banco copiado ausente." if not dump_sha else "Resumo do banco copiado diferente."),
    )
    name = restore_db_name()
    _drop_database()
    with owner_connect(autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(name)))
    params = owner_params(name)
    result = subprocess.run(  # noqa: S603 - executável e argumentos fixos
        [
            settings.PG_RESTORE,
            "--no-owner",
            "--no-privileges",
            "--exit-on-error",
            "--no-password",
            f"--dbname={name}",
            str(dump),
        ],
        env=pg_env(params),
        capture_output=True,
        text=True,
        timeout=RESTORE_TIMEOUT,
        check=False,
    )
    _check(
        checks,
        "C3",
        result.returncode == 0,
        f"Restaurado em {name}."
        if result.returncode == 0
        else f"pg_restore falhou: {result.stderr.strip()[-400:]}",
    )
    with owner_connect(name) as conn, conn.cursor() as cursor:
        restored = table_counts(cursor)
    expected_counts = manifest["tabelas"]
    diffs = sorted(
        name_
        for name_ in set(expected_counts) | set(restored)
        if expected_counts.get(name_) != restored.get(name_)
    )
    _check(
        checks,
        "C4",
        not diffs,
        f"{len(restored)} tabelas e {sum(restored.values())} linhas iguais ao manifesto."
        if not diffs
        else "Divergência em: "
        + ", ".join(f"{t} ({expected_counts.get(t)} → {restored.get(t)})" for t in diffs[:10]),
        stop=False,
    )
    count, breaks, head_seq, head_hash = _walk_restored_chain(name)
    trail = manifest["trilha"]
    head_ok = (head_seq or 0) == (trail["seq"] or 0) and (head_hash or "") == (trail["hash"] or "")
    _check(
        checks,
        "C5",
        not breaks and head_ok,
        f"{count} eventos íntegros; último {head_seq}."
        if not breaks and head_ok
        else (
            _describe_breaks(breaks)
            if breaks
            else f"Último evento {head_seq} difere do manifesto ({trail['seq']})."
        ),
        stop=False,
    )
    missing, altered = [], []
    for sha, _size in manifest["arquivos"]["lista"]:
        path = pool_path(sha)
        if not path.is_file():
            missing.append(sha)
        elif sha256_file(path) != sha:
            altered.append(sha)
    with owner_connect(name) as conn, conn.cursor() as cursor:
        from sgp.files.models import StoredFile

        cursor.execute(
            sql.SQL("SELECT DISTINCT sha256 FROM {}").format(
                sql.Identifier(StoredFile._meta.db_table)
            )
        )
        referenced = {row[0] for row in cursor.fetchall()}
    listed = {sha for sha, _size in manifest["arquivos"]["lista"]}
    unlisted = sorted(referenced - listed)
    ok = not missing and not altered and not unlisted
    detail = f"{len(listed)} arquivo(s) conferido(s)."
    if not ok:
        parts = []
        if missing:
            parts.append("ausentes: " + ", ".join(s[:12] for s in missing[:10]))
        if altered:
            parts.append("alterados: " + ", ".join(s[:12] for s in altered[:10]))
        if unlisted:
            parts.append("fora do manifesto: " + ", ".join(s[:12] for s in unlisted[:10]))
        detail = "Arquivos " + "; ".join(parts) + "."
    _check(checks, "C6", ok, detail, stop=False)


def _describe_breaks(breaks: list[dict]) -> str:
    """Quebras da cadeia restaurada, avisando se a verificação da trilha em uso já as apontava
    (a cópia reproduz fielmente um incidente que já existia no banco em uso)."""
    from sgp.audit.services import BREAK_LABELS, latest_verification

    shown = ", ".join(
        f"evento {b['seq']} ({BREAK_LABELS.get(b['kind'], b['kind']).lower()})" for b in breaks[:5]
    )
    text = f"{len(breaks)} quebra(s) na cadeia restaurada: {shown}."
    live = latest_verification()
    known = {(b.get("seq"), b.get("kind")) for b in (live.breaks if live else [])}
    if known and all((b["seq"], b["kind"]) in known for b in breaks):
        text += (
            " A verificação da trilha do banco em uso já aponta a(s) mesma(s) quebra(s): "
            "incidente existente, reproduzido fielmente pela cópia."
        )
    return text


def _walk_restored_chain(name: str):
    """Reaproveita a verificação da trilha (feature 001) sobre as linhas do banco restaurado."""
    columns = sql.SQL(", ").join(sql.Identifier(field) for field in (*HASH_FIELDS, "hash"))
    query = sql.SQL("SELECT {} FROM {} ORDER BY seq").format(
        columns, sql.Identifier(AuditEvent._meta.db_table)
    )
    with owner_connect(name) as conn:
        with conn.cursor(name="trilha_restaurada") as cursor:
            cursor.itersize = 2000
            cursor.execute(query)
            return walk_rows(cursor)


def _drop_database() -> None:
    name = restore_db_name()
    try:
        with owner_connect(autocommit=True) as conn:
            conn.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name))
            )
    except Exception:  # noqa: BLE001 - o descarte não pode esconder o resultado do teste
        logger.exception("Não foi possível descartar o banco isolado %s", name)


def _finish(test: RestoreTest, checks: list, passed: bool, error: str) -> RestoreTest:
    with transaction.atomic():
        RestoreTest.objects.filter(pk=test.pk).update(
            status=RestoreStatus.PASSED if passed else RestoreStatus.FAILED,
            finished_at=timezone.now(),
            checks=checks,
            error="" if passed else error[:2000],
        )
        test.refresh_from_db()
        record_event(
            "operations.restore_tested",
            actor=test.requested_by,
            obj=test,
            new_value={
                "aprovado": passed,
                "copia": test.backup.label if test.backup else None,
                "conferencias": {c["codigo"]: c["aprovado"] for c in checks},
            },
            reason="" if passed else error[:500],
        )
        if not passed:
            alerts.notify_admins(
                "Teste de restauração reprovado",
                "O teste de restauração da cópia "
                f"{test.backup.label if test.backup else '(nenhuma)'} reprovou.\n\n"
                f"Motivo: {error}\n\nVeja o painel Operação e validação do SGP-P&D.",
            )
    return test


def latest_test() -> RestoreTest | None:
    return RestoreTest.objects.exclude(status=RestoreStatus.RUNNING).order_by("-started_at").first()


def check_freshness(now=None) -> bool:
    """Avisa se não há cópia bem-sucedida nas últimas BACKUP_MAX_AGE_HOURS horas (FR-008)."""
    now = now or timezone.now()
    limit = now - timedelta(hours=settings.BACKUP_MAX_AGE_HOURS)
    latest = (
        BackupRun.objects.filter(status=BackupStatus.SUCCESS)
        .order_by("-finished_at", "-pk")
        .first()
    )
    if latest is not None and latest.finished_at and latest.finished_at >= limit:
        return True
    when = (
        f"{timezone.localtime(latest.finished_at):%d/%m/%Y %H:%M}"
        if latest is not None and latest.finished_at
        else "nunca"
    )
    with transaction.atomic():
        record_event(
            "operations.backup_stale",
            actor=None,
            object_type="operations.backuprun",
            object_id=str(latest.pk) if latest else "",
            object_repr=str(latest) if latest else "sem cópia",
            new_value={"ultima_bem_sucedida": latest.finished_at if latest else None},
            reason=f"Sem cópia bem-sucedida nas últimas {settings.BACKUP_MAX_AGE_HOURS} horas.",
        )
        alerts.notify_admins(
            "Cópia de segurança atrasada",
            f"Não há cópia de segurança bem-sucedida nas últimas {settings.BACKUP_MAX_AGE_HOURS} "
            f"horas (última: {when}).\n\nConfira o worker, o agendador e o destino das cópias.",
        )
    return False
