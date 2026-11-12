"""Itens da qualificação de instalação (FR-011 da feature 014, research R8).

Nenhum item mostra valores de segredos: as variáveis obrigatórias são conferidas só pela presença.
"""

import importlib.metadata
import os
import re
import shutil
import subprocess
import sys
import tomllib
from datetime import UTC, datetime
from pathlib import Path

from django.conf import settings
from django.core import checks as django_checks
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from sgp.core.db_privileges import DELETABLE_TABLES, append_only_tables

from . import backup, version
from .checks import APPROVED, FAILED, Item, run_items, tcp_reachable, uri_host_port, worker_ping

REQUIRED_ENV = (
    "DJANGO_SECRET_KEY",
    "DB_PASSWORD",
    "DB_OWNER_PASSWORD",
    "LDAP_SERVER_URI",
    "EMAIL_HOST",
    "DEFAULT_FROM_EMAIL",
    "DOCUMENT_SEAL_PKCS12",
    "DOCUMENT_SEAL_PASSWORD",
    "BACKUP_DIR",
    "SITE_URL",
)
# Avisos do `check --deploy` atendidos pelo nginx (redireciona para HTTPS e envia HSTS).
DEPLOY_WARNINGS_IN_PROXY = {"security.W004", "security.W008"}
REQUIRED_FONTS = ("Carlito", "DejaVu")
REQUIRED_JOBS = (
    "verificacao-diaria-da-trilha",
    "copia-de-seguranca-diaria",
    "teste-de-restauracao-mensal",
    "conferencia-de-copias-em-dia",
)


def _system_version():
    info = version.current()
    if not info["commit"]:
        return FAILED, f"Versão {info['versao'] or '?'} sem commit (defina SGP_COMMIT no build)."
    return APPROVED, f"Versão {info['versao']}, commit {info['commit'][:12]}."


def _python():
    current = ".".join(str(part) for part in sys.version_info[:3])
    ok = sys.version_info[:2] == (3, 12)
    return (APPROVED if ok else FAILED), f"Python {current} (esperado 3.12)."


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _packages():
    lock_path = Path(settings.BASE_DIR) / "uv.lock"
    lock = tomllib.loads(lock_path.read_text("utf-8"))
    locked = {
        _normalize(package["name"]): str(package.get("version", ""))
        for package in lock.get("package", [])
        if package.get("version")
    }
    checked, mismatches = 0, []
    for dist in importlib.metadata.distributions():
        name = _normalize(dist.metadata["Name"] or "")
        if name not in locked:
            continue
        checked += 1
        if dist.version != locked[name]:
            mismatches.append(f"{name} {dist.version} (fixado {locked[name]})")
    if mismatches:
        return FAILED, "Diferente do uv.lock: " + "; ".join(sorted(mismatches)[:15])
    django_version = importlib.metadata.version("django")
    return APPROVED, f"{checked} pacotes iguais ao uv.lock (Django {django_version})."


def _database():
    with connection.cursor() as cursor:
        cursor.execute("SHOW server_version")
        server = cursor.fetchone()[0]
        cursor.execute("SHOW TimeZone")
        zone = cursor.fetchone()[0]
        cursor.execute("SHOW server_encoding")
        encoding = cursor.fetchone()[0]
    ok = server.startswith("17") and zone in ("UTC", "Etc/UTC") and encoding == "UTF8"
    return (
        APPROVED if ok else FAILED
    ), f"PostgreSQL {server}, fuso {zone}, codificação {encoding} (esperado 17, UTC, UTF8)."


def _migrations():
    executor = MigrationExecutor(connection)
    plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
    if plan:
        pending = ", ".join(f"{m.app_label}.{m.name}" for m, _ in plan[:10])
        return FAILED, f"{len(plan)} migração(ões) pendente(s): {pending}."
    return APPROVED, "Todas as migrações aplicadas."


def _deploy_checks():
    messages = django_checks.run_checks(include_deployment_checks=True)
    relevant = [
        m
        for m in messages
        if m.level >= django_checks.WARNING and m.id not in DEPLOY_WARNINGS_IN_PROXY
    ]
    if relevant:
        return FAILED, "; ".join(f"{m.id}: {str(m.msg)[:120]}" for m in relevant[:8])
    return APPROVED, "Sem pendências (HTTPS e HSTS aplicados pelo nginx)."


def _debug_off():
    if settings.DEBUG:
        return FAILED, "Modo de depuração ligado (DJANGO_DEBUG)."
    return APPROVED, "Modo de depuração desligado."


def _secret_key():
    key = settings.SECRET_KEY or ""
    weak = (
        len(key) < 50
        or len(set(key)) < 5
        or re.search(r"dev|teste|test|insecure|troque", key, re.I)
    )
    if weak:
        return FAILED, "Chave secreta curta ou de desenvolvimento (valor não exibido)."
    return APPROVED, "Chave secreta com 50 ou mais caracteres (valor não exibido)."


def _https():
    problems = []
    if not settings.SESSION_COOKIE_SECURE or not settings.CSRF_COOKIE_SECURE:
        problems.append("cookies sem a marca Secure")
    if not str(settings.SITE_URL).startswith("https://"):
        problems.append("SITE_URL fora de HTTPS")
    if problems:
        return FAILED, "; ".join(problems).capitalize() + "."
    return APPROVED, f"Cookies seguros; endereço {settings.SITE_URL}."


def _locale():
    ok = (
        settings.TIME_ZONE == "America/Sao_Paulo"
        and settings.USE_TZ
        and settings.LANGUAGE_CODE == "pt-br"
    )
    detail = f"Fuso {settings.TIME_ZONE}, datas em UTC={settings.USE_TZ}, idioma {settings.LANGUAGE_CODE}."
    return (APPROVED if ok else FAILED), detail


def _environment():
    missing = [name for name in REQUIRED_ENV if not (os.environ.get(name) or "").strip()]
    if missing:
        return FAILED, "Ausentes: " + ", ".join(missing) + " (valores nunca exibidos)."
    return APPROVED, f"{len(REQUIRED_ENV)} variáveis presentes (valores nunca exibidos)."


def _triggers():
    expected = set(append_only_tables())
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT c.relname FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid "
            "JOIN pg_proc p ON p.oid = t.tgfoid "
            "WHERE p.proname = 'sgp_forbid_change' AND NOT t.tgisinternal"
        )
        present = {row[0] for row in cursor.fetchall()}
    missing = sorted(expected - present)
    if missing:
        return FAILED, "Sem gatilho de imutabilidade: " + ", ".join(missing) + "."
    return APPROVED, f"{len(expected)} tabelas somente de inclusão com gatilho."


def _privileges():
    role = settings.DB_APP_ROLE
    append_only = set(append_only_tables())
    problems = []
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", [role])
        if cursor.fetchone() is None:
            return FAILED, f"Papel da aplicação {role} inexistente."
        cursor.execute(
            "SELECT tablename, has_table_privilege(%s, quote_ident(tablename), 'DELETE'), "
            "has_table_privilege(%s, quote_ident(tablename), 'UPDATE'), "
            "has_table_privilege(%s, quote_ident(tablename), 'TRUNCATE') "
            "FROM pg_tables WHERE schemaname = 'public'",
            [role, role, role],
        )
        rows = cursor.fetchall()
    for table, can_delete, can_update, can_truncate in rows:
        if can_delete and table not in DELETABLE_TABLES:
            problems.append(f"DELETE em {table}")
        if can_update and table in append_only:
            problems.append(f"UPDATE em {table}")
        if can_truncate:
            problems.append(f"TRUNCATE em {table}")
    if problems:
        return FAILED, f"Papel {role} com privilégio indevido: " + ", ".join(problems[:10]) + "."
    return (
        APPROVED,
        f"Papel {role} sem DELETE, sem UPDATE nas {len(append_only)} tabelas somente de inclusão e sem TRUNCATE.",
    )


def _owner_createdb():
    with backup.owner_connect(autocommit=True) as conn:
        allowed = conn.execute(
            "SELECT rolcreatedb OR rolsuper FROM pg_roles WHERE rolname = current_user"
        ).fetchone()[0]
    if not allowed:
        return FAILED, "O papel dono não pode criar o banco isolado do teste de restauração."
    return APPROVED, "Papel dono pode criar e descartar o banco isolado."


def _seal_certificate():
    from sgp.documents import seal

    try:
        signer = seal.load_signer()
    except seal.SealError as exc:
        return FAILED, str(exc)
    certificate = signer.signing_cert
    expires = certificate.not_valid_after
    days = (expires - datetime.now(UTC)).days
    detail = f"Válido até {expires:%d/%m/%Y} ({days} dias); titular {certificate.subject.human_friendly}."
    return APPROVED, detail


def _backup_destination():
    try:
        target = backup.check_destination()
    except backup.BackupError as exc:
        return FAILED, str(exc)
    media = Path(settings.MEDIA_ROOT)
    media.mkdir(parents=True, exist_ok=True)
    if os.stat(target).st_dev == os.stat(media).st_dev:
        return FAILED, f"{target} fica no mesmo sistema de arquivos dos dados ({media})."
    return APPROVED, f"{target} gravável e em outro sistema de arquivos que os dados."


def _pg_tools():
    with connection.cursor() as cursor:
        cursor.execute("SHOW server_version_num")
        server_major = int(cursor.fetchone()[0]) // 10000
    found = []
    for tool in (settings.PG_DUMP, settings.PG_RESTORE):
        if shutil.which(tool) is None:
            return FAILED, f"{tool} não encontrado."
        output = subprocess.run(  # noqa: S603 - executável e argumento fixos
            [tool, "--version"], capture_output=True, text=True, check=False, timeout=10
        ).stdout.strip()
        match = re.search(r"(\d+)\.", output)
        major = int(match.group(1)) if match else 0
        if major != server_major:
            return FAILED, f"{output} difere da versão do servidor ({server_major})."
        found.append(output)
    return APPROVED, "; ".join(found) + "."


def _generation_tools():
    import weasyprint

    fc_list = shutil.which("fc-list")
    listing = ""
    if fc_list:
        listing = subprocess.run(  # noqa: S603 - ferramenta do sistema, sem entrada externa
            [fc_list], capture_output=True, text=True, check=False, timeout=10
        ).stdout
    missing = [font for font in REQUIRED_FONTS if font.lower() not in listing.lower()]
    if missing:
        return FAILED, "Fontes ausentes: " + ", ".join(missing) + "."
    return APPROVED, f"WeasyPrint {weasyprint.__version__}; fontes {', '.join(REQUIRED_FONTS)}."


def _media_writable():
    media = Path(settings.MEDIA_ROOT)
    if not media.is_dir() or not os.access(media, os.W_OK):
        return FAILED, f"Armazenamento de arquivos {media} indisponível ou sem gravação."
    return APPROVED, f"Armazenamento de arquivos {media} gravável."


def _broker():
    from config.celery import app

    with app.connection_for_write() as conn:
        conn.ensure_connection(max_retries=1, timeout=3)
    return APPROVED, "Fila de tarefas (Redis) acessível."


def _worker_and_schedule():
    missing = [job for job in REQUIRED_JOBS if job not in settings.CELERY_BEAT_SCHEDULE]
    if missing:
        return FAILED, "Agendamentos ausentes: " + ", ".join(missing) + "."
    workers = worker_ping()
    if not workers:
        return FAILED, "Nenhum worker respondeu (tarefas e agendador parados)."
    return (
        APPROVED,
        f"Worker(s) {', '.join(workers)}; {len(settings.CELERY_BEAT_SCHEDULE)} agendamentos.",
    )


def _ldap():
    uri = (getattr(settings, "AUTH_LDAP_SERVER_URI", "") or "").strip()
    if not uri:
        return FAILED, "Diretório (LDAP_SERVER_URI) não configurado."
    host, port = uri_host_port(uri, 636 if uri.startswith("ldaps") else 389)
    ok, detail = tcp_reachable(host, port)
    return (APPROVED if ok else FAILED), f"Diretório {detail}"


def _email():
    backend = settings.EMAIL_BACKEND
    if not backend.endswith("smtp.EmailBackend"):
        return FAILED, f"Envio de e-mail não configurado para SMTP ({backend.rsplit('.', 1)[-1]})."
    ok, detail = tcp_reachable(settings.EMAIL_HOST, int(settings.EMAIL_PORT))
    return (APPROVED if ok else FAILED), f"Servidor de e-mail {detail}"


def _static_files():
    manifest = Path(settings.STATIC_ROOT) / "staticfiles.json"
    if not manifest.is_file():
        return FAILED, "Arquivos estáticos não coletados (collectstatic)."
    return APPROVED, "Arquivos estáticos coletados com manifesto."


ITEMS: list[Item] = [
    ("IQ-01", "Versão do sistema identificada (versão e commit)", _system_version),
    ("IQ-02", "Python da versão fixada", _python),
    ("IQ-03", "Pacotes instalados iguais aos fixados no repositório (uv.lock)", _packages),
    ("IQ-04", "PostgreSQL 17 com fuso UTC e codificação UTF8", _database),
    ("IQ-05", "Migrações do banco aplicadas", _migrations),
    ("IQ-06", "Verificações de implantação do Django", _deploy_checks),
    ("IQ-07", "Modo de depuração desligado", _debug_off),
    ("IQ-08", "Chave secreta de produção", _secret_key),
    ("IQ-09", "Cookies seguros e endereço em HTTPS", _https),
    ("IQ-10", "Fuso de exibição, datas em UTC e idioma", _locale),
    ("IQ-11", "Variáveis de ambiente obrigatórias presentes", _environment),
    ("IQ-12", "Gatilhos de imutabilidade nas tabelas somente de inclusão", _triggers),
    ("IQ-13", "Privilégios do papel da aplicação no banco", _privileges),
    ("IQ-14", "Papel dono habilitado para o teste de restauração", _owner_createdb),
    ("IQ-15", "Certificado do selo legível e válido", _seal_certificate),
    ("IQ-16", "Destino das cópias de segurança separado dos dados", _backup_destination),
    ("IQ-17", "pg_dump e pg_restore da versão do servidor", _pg_tools),
    ("IQ-18", "Ferramentas e fontes da geração de documentos", _generation_tools),
    ("IQ-19", "Armazenamento de arquivos gravável", _media_writable),
    ("IQ-20", "Fila de tarefas acessível", _broker),
    ("IQ-21", "Worker e agendamentos ativos", _worker_and_schedule),
    ("IQ-22", "Diretório (LDAP) acessível", _ldap),
    ("IQ-23", "Servidor de e-mail acessível", _email),
    ("IQ-24", "Arquivos estáticos coletados", _static_files),
]


def run() -> list[dict]:
    return run_items(ITEMS)
