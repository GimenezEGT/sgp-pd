"""Cópia de segurança diária: instantâneo consistente do banco, acervo de arquivos endereçado pelo
conteúdo, manifesto e retenção (research R1 a R4 e contrato copia-e-manifesto.md da feature 014).

Nada do banco em uso é alterado; a retenção remove só pastas de cópias diárias antigas no destino
(nunca o acervo de arquivos nem registros do sistema) e registra cada remoção na trilha.
"""

import hashlib
import json
import logging
import os
import shutil
import subprocess
import tempfile
from datetime import UTC, timedelta
from pathlib import Path

import psycopg
from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone
from psycopg import sql

from sgp.audit.models import AuditEvent
from sgp.audit.services import record_event
from sgp.files.models import StoredFile

from . import alerts, version
from .models import BackupRun, BackupStatus, RunKind

logger = logging.getLogger(__name__)

BACKUP_LOCK = 0x53475001  # uma cópia por vez (bloqueio consultivo de sessão)
CHUNK = 1024 * 1024
DUMP = "banco.dump"
MANIFEST = "manifesto.json"
MANIFEST_FORMAT = 1
DUMP_TIMEOUT = 6 * 3600


class BackupError(Exception):
    """Falha da cópia, com o motivo para a tela, a trilha e o aviso."""


class BackupBusy(BackupError):
    """Já há uma cópia em andamento."""


class BackupIncomplete(BackupError):
    """Banco copiado, mas há arquivo guardado ausente ou alterado: a cópia reprova e a pasta fica
    (o banco copiado continua disponível para recuperação de emergência)."""


# ------------------------------------------------------------------ destino e conexões


def destination() -> Path:
    return Path(settings.BACKUP_DIR)


def copies_dir() -> Path:
    return destination() / "copias"


def pool_dir() -> Path:
    return destination() / "arquivos"


def pool_path(sha256: str) -> Path:
    return pool_dir() / sha256[:2] / sha256[2:4] / sha256


def check_destination() -> Path:
    """Destino existente, gravável e fora do diretório dos dados (FR-003)."""
    target = destination().resolve()
    media = Path(settings.MEDIA_ROOT).resolve()
    if not target.is_dir():
        raise BackupError(f"Destino de cópias inexistente ou indisponível: {target}.")
    if target == media or media in target.parents or target in media.parents:
        raise BackupError(
            "O destino de cópias não pode ser o diretório dos dados, ficar dentro dele nem contê-lo."
        )
    if not os.access(target, os.W_OK):
        raise BackupError(f"Sem permissão de gravação no destino de cópias: {target}.")
    return target


def owner_params(dbname: str | None = None) -> dict:
    """Conexão do papel dono (o mesmo das migrações), só de variáveis de ambiente."""
    db = connection.settings_dict
    return {
        "host": db.get("HOST") or "localhost",
        "port": str(db.get("PORT") or "5432"),
        "dbname": dbname or db["NAME"],
        "user": settings.DB_OWNER_USER,
        "password": settings.DB_OWNER_PASSWORD,
    }


def owner_connect(dbname: str | None = None, **kwargs) -> psycopg.Connection:
    return psycopg.connect(**owner_params(dbname), connect_timeout=10, **kwargs)


def pg_env(params: dict) -> dict:
    env = dict(os.environ)
    env.update(
        {
            "PGHOST": params["host"],
            "PGPORT": params["port"],
            "PGUSER": params["user"],
            "PGPASSWORD": params["password"],
            "PGDATABASE": params["dbname"],
        }
    )
    return env


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def table_counts(cursor) -> dict[str, int]:
    cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
    names = [row[0] for row in cursor.fetchall()]
    counts = {}
    for name in names:
        cursor.execute(sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(name)))
        counts[name] = cursor.fetchone()[0]
    return counts


class AdvisoryLock:
    """Bloqueio consultivo numa sessão própria do papel dono; solto ao fechar a conexão."""

    def __init__(self, key: int, busy_message: str, busy_error=BackupBusy):
        self.key = key
        self.busy_message = busy_message
        self.busy_error = busy_error
        self.conn = None

    def __enter__(self):
        self.conn = owner_connect(autocommit=True)
        acquired = self.conn.execute("SELECT pg_try_advisory_lock(%s)", [self.key]).fetchone()[0]
        if not acquired:
            self.conn.close()
            raise self.busy_error(self.busy_message)
        return self

    def __exit__(self, *exc):
        if self.conn is not None:
            self.conn.close()
        return False


def is_running() -> bool:
    """Há uma cópia em andamento (bloqueio consultivo ocupado)?"""
    try:
        with AdvisoryLock(BACKUP_LOCK, ""):
            return False
    except BackupBusy:
        return True


# ------------------------------------------------------------------ cópia


def run_backup(*, kind: str = RunKind.SCHEDULED, by=None) -> BackupRun:
    """Executa a cópia; levanta BackupBusy se houver outra em andamento (nada é registrado)."""
    with AdvisoryLock(BACKUP_LOCK, "Já há uma cópia de segurança em andamento."):
        record = BackupRun.objects.create(
            kind=kind, requested_by=by, system_version=version.display()
        )
        folder = None
        try:
            folder = _new_folder(record)
            _run(record, folder)
        except BackupIncomplete as exc:
            return _fail(record, str(exc), folder, keep_folder=True)
        except BackupError as exc:
            return _fail(record, str(exc), folder)
        except Exception as exc:  # noqa: BLE001 - toda falha vira registro, trilha e aviso
            logger.exception("Falha inesperada na cópia de segurança %s", record.pk)
            return _fail(record, f"Erro inesperado: {exc.__class__.__name__}: {exc}", folder)
    prune()
    record.refresh_from_db()
    return record


def _new_folder(record: BackupRun) -> Path:
    check_destination()
    label = timezone.localtime(record.started_at).strftime("%Y%m%d-%H%M%S")
    folder = copies_dir() / label
    if folder.exists():
        label = f"{label}-{record.pk}"
        folder = copies_dir() / label
    folder.mkdir(parents=True)
    BackupRun.objects.filter(pk=record.pk).update(label=label)
    record.label = label
    return folder


def _run(record: BackupRun, folder: Path) -> None:
    params = owner_params()
    dump = folder / DUMP
    audit_table = AuditEvent._meta.db_table
    files_table = StoredFile._meta.db_table
    with owner_connect() as conn:
        conn.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
        conn.read_only = True
        with conn.cursor() as cursor:
            cursor.execute("SELECT pg_export_snapshot()")
            snapshot = cursor.fetchone()[0]
            counts = table_counts(cursor)
            cursor.execute("SHOW server_version")
            server = cursor.fetchone()[0]
            cursor.execute(
                sql.SQL("SELECT seq, hash FROM {} ORDER BY seq DESC LIMIT 1").format(
                    sql.Identifier(audit_table)
                )
            )
            head = cursor.fetchone()
            cursor.execute(
                sql.SQL(
                    "SELECT DISTINCT ON (sha256) sha256, size, storage_name FROM {} "
                    "ORDER BY sha256, id"
                ).format(sql.Identifier(files_table))
            )
            files = cursor.fetchall()
        result = subprocess.run(  # noqa: S603 - executável e argumentos fixos
            [
                settings.PG_DUMP,
                "--format=custom",
                f"--snapshot={snapshot}",
                "--no-password",
                f"--file={dump}",
                params["dbname"],
            ],
            env=pg_env(params),
            capture_output=True,
            text=True,
            timeout=DUMP_TIMEOUT,
            check=False,
        )
        conn.rollback()
    if result.returncode != 0:
        raise BackupError(f"pg_dump falhou: {result.stderr.strip()[-500:]}")
    copied, total_bytes, missing, altered = _copy_files(files)
    database_sha = sha256_file(dump)
    manifest = {
        "formato": MANIFEST_FORMAT,
        "sistema": version.current(),
        "criado_em": record.started_at.astimezone(UTC).isoformat(),
        "banco": {
            "arquivo": DUMP,
            "tamanho": dump.stat().st_size,
            "sha256": database_sha,
            "servidor": server,
            "nome": params["dbname"],
        },
        "tabelas": counts,
        "trilha": {"seq": head[0] if head else 0, "hash": head[1] if head else ""},
        "arquivos": {
            "total": len(files),
            "novos": copied,
            "bytes": total_bytes,
            "lista": [[sha, size] for sha, size, _ in files],
            "problemas": [[sha, "ausente"] for sha in missing]
            + [[sha, "alterado"] for sha in altered],
        },
    }
    data = json.dumps(manifest, ensure_ascii=False, indent=1).encode("utf-8")
    (folder / MANIFEST).write_bytes(data)
    manifest_sha = hashlib.sha256(data).hexdigest()
    finished = timezone.now()
    details = {
        "database_size": manifest["banco"]["tamanho"],
        "database_sha256": database_sha,
        "server_version": server,
        "table_counts": counts,
        "audit_head_seq": manifest["trilha"]["seq"] or None,
        "audit_head_hash": manifest["trilha"]["hash"],
        "files_total": len(files),
        "files_new": copied,
        "files_bytes": total_bytes,
        "manifest_sha256": manifest_sha,
    }
    if missing or altered:
        BackupRun.objects.filter(pk=record.pk).update(**details)
        parts = []
        if missing:
            parts.append(
                f"{len(missing)} ausente(s) do armazenamento: "
                + ", ".join(sha[:12] for sha in missing[:10])
            )
        if altered:
            parts.append(
                f"{len(altered)} com conteúdo diferente do resumo guardado no sistema: "
                + ", ".join(sha[:12] for sha in altered[:10])
            )
        raise BackupIncomplete(
            "Banco copiado e manifesto gravado, mas há arquivo(s) guardado(s) com problema — "
            + "; ".join(parts)
            + ". Abra um registro de incidente; a pasta da cópia fica para recuperação."
        )
    with transaction.atomic():
        BackupRun.objects.filter(pk=record.pk).update(
            status=BackupStatus.SUCCESS,
            finished_at=finished,
            monthly=_first_of_month(record),
            **details,
        )
        record.refresh_from_db()
        record_event(
            "operations.backup_completed",
            actor=record.requested_by,
            obj=record,
            new_value={
                "pasta": record.label,
                "banco_bytes": record.database_size,
                "banco_sha256": database_sha,
                "manifesto_sha256": manifest_sha,
                "tabelas": len(counts),
                "trilha_seq": record.audit_head_seq,
                "arquivos": len(files),
                "arquivos_novos": copied,
                "mensal": record.monthly,
            },
        )


def _copy_files(files) -> tuple[int, int, list[str], list[str]]:
    copied, total_bytes, missing, altered = 0, 0, [], []
    media = Path(settings.MEDIA_ROOT)
    for sha, size, storage_name in files:
        total_bytes += size
        target = pool_path(sha)
        if target.exists():
            continue
        source = media / storage_name
        if not source.is_file():
            missing.append(sha)
            continue
        if _copy_verified(source, target, sha):
            copied += 1
        else:
            altered.append(sha)
    return copied, total_bytes, missing, altered


def _copy_verified(source: Path, target: Path, expected: str) -> bool:
    """Copia conferindo o resumo; conteúdo divergente não entra no acervo (devolve False)."""
    target.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    handle, temp_name = tempfile.mkstemp(dir=target.parent, prefix=".copiando-")
    try:
        with os.fdopen(handle, "wb") as out, source.open("rb") as src:
            while chunk := src.read(CHUNK):
                digest.update(chunk)
                out.write(chunk)
            out.flush()
            os.fsync(out.fileno())
        if digest.hexdigest() != expected:
            return False
        os.replace(temp_name, target)
        return True
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _first_of_month(record: BackupRun) -> bool:
    local = timezone.localtime(record.started_at)
    start = local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = (start + timedelta(days=32)).replace(day=1)
    return (
        not BackupRun.objects.filter(
            status=BackupStatus.SUCCESS, started_at__gte=start, started_at__lt=end
        )
        .exclude(pk=record.pk)
        .exists()
    )


def _fail(
    record: BackupRun, reason: str, folder: Path | None, *, keep_folder: bool = False
) -> BackupRun:
    if folder is not None and folder.exists() and not keep_folder:
        shutil.rmtree(folder, ignore_errors=True)  # pasta incompleta não é cópia válida
    with transaction.atomic():
        BackupRun.objects.filter(pk=record.pk).update(
            status=BackupStatus.FAILED, finished_at=timezone.now(), error=reason[:2000]
        )
        record.refresh_from_db()
        record_event(
            "operations.backup_failed",
            actor=record.requested_by,
            obj=record,
            new_value={"pasta": record.label},
            reason=reason[:500],
        )
        alerts.notify_admins(
            "Falha na cópia de segurança",
            "A cópia de segurança iniciada em "
            f"{timezone.localtime(record.started_at):%d/%m/%Y %H:%M} falhou.\n\n"
            f"Motivo: {reason}\n\nDestino: {settings.BACKUP_DIR}\n"
            "Veja o painel Operação e validação do SGP-P&D.",
        )
    return record


# ------------------------------------------------------------------ retenção


def prune(now=None) -> list[BackupRun]:
    """Remove as pastas das cópias diárias mais antigas que BACKUP_KEEP_DAYS, exceto a mensal."""
    now = now or timezone.now()
    limit = now - timedelta(days=settings.BACKUP_KEEP_DAYS)
    removed = []
    candidates = BackupRun.objects.filter(
        status__in=(BackupStatus.SUCCESS, BackupStatus.FAILED),
        removed_at__isnull=True,
        monthly=False,
        started_at__lt=limit,
    ).order_by("started_at")
    for run in candidates:
        folder = copies_dir() / run.label if run.label else None
        if folder is None or not folder.exists():
            continue  # cópia que falhou sem pasta: nada a remover
        shutil.rmtree(folder)
        with transaction.atomic():
            BackupRun.objects.filter(pk=run.pk).update(removed_at=now)
            run.refresh_from_db()
            record_event(
                "operations.backup_removed",
                actor=None,
                obj=run,
                new_value={"pasta": run.label, "inicio": run.started_at},
                reason=f"Retenção de {settings.BACKUP_KEEP_DAYS} dias para cópias diárias.",
            )
        removed.append(run)
    return removed


def latest_success() -> BackupRun | None:
    return (
        BackupRun.objects.filter(status=BackupStatus.SUCCESS, removed_at__isnull=True)
        .order_by("-started_at", "-pk")
        .first()
    )
