"""Configuração do SGP-P&D.

Todos os valores sensíveis ou dependentes do ambiente vêm de variáveis de ambiente
(contrato em specs/001-fundacao-acesso-auditoria/contracts/configuracao.md).
"""

import os
from pathlib import Path

from celery.schedules import crontab
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def env_str(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "sim", "on"}


def env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ImproperlyConfigured(f"A variável {name} deve ser um número inteiro.") from exc


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    raise ImproperlyConfigured("Defina DJANGO_SECRET_KEY no ambiente.")

DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", "https://localhost")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "sgp.core",
    "sgp.accounts",
    "sgp.audit",
    "sgp.vocab",
    "sgp.projects",
    "sgp.files",
    "sgp.catalog",
    "sgp.formtemplates",
    "sgp.subdocuments",
    "sgp.signatures",
    "sgp.documents",
    "sgp.revisions",
    "sgp.studies",
    "sgp.notebook",
    "sgp.fulldoc",
    "sgp.notifications",
    "sgp.dashboard",
    "sgp.dossier",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "sgp.core.request_context.RequestContextMiddleware",
    "sgp.core.middleware.InactivityTimeoutMiddleware",
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
    "sgp.accounts.middleware.ProfileRequiredMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "sgp.core.context_processors.sgp",
            ],
        },
    }
]

# Banco: o papel da aplicação (DB_USER) não tem DELETE nem UPDATE nas tabelas append-only.
# Migrações e privilégios rodam com o papel dono (DB_OWNER_USER), pelo entrypoint.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": env_str("DB_HOST", "db"),
        "PORT": env_str("DB_PORT", "5432"),
        "NAME": env_str("DB_NAME", "sgp"),
        "USER": env_str("DB_USER", "sgp_app"),
        "PASSWORD": env_str("DB_PASSWORD", ""),
        "ATOMIC_REQUESTS": True,
        "CONN_MAX_AGE": env_int("DB_CONN_MAX_AGE", 60),
        "OPTIONS": {"connect_timeout": 5},
    }
}
DB_APP_ROLE = env_str("DB_APP_ROLE", "sgp_app")
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Autenticação: somente Active Directory (LDAP); não há contas locais nem senhas guardadas.
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ["sgp.accounts.ldap.SGPLDAPBackend"]
AUTH_PASSWORD_VALIDATORS = []
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "core:home"
LOGOUT_REDIRECT_URL = "accounts:login"

from sgp.accounts.ldap_config import build_ldap_settings  # noqa: E402

globals().update(build_ldap_settings(os.environ))

# Sessão no servidor; a inatividade é controlada pelo InactivityTimeoutMiddleware.
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_IDLE_TIMEOUT_MINUTES = env_int("SESSION_IDLE_TIMEOUT_MINUTES", 30)
SESSION_COOKIE_AGE = 12 * 60 * 60
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True
SECURE_COOKIES = env_bool("DJANGO_SECURE_COOKIES", True)
SESSION_COOKIE_SECURE = SECURE_COOKIES
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_NAME = "sgp_sessao"
CSRF_COOKIE_SECURE = SECURE_COOKIES
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_NAME = "sgp_csrf"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# Bloqueio de login e trilha de auditoria
LOGIN_MAX_FAILURES = env_int("LOGIN_MAX_FAILURES", 5)
LOGIN_LOCKOUT_MINUTES = env_int("LOGIN_LOCKOUT_MINUTES", 15)
AUDIT_VERIFY_HOUR = env_int("AUDIT_VERIFY_HOUR", 2)
AUDIT_VERIFY_MINUTE = env_int("AUDIT_VERIFY_MINUTE", 0)
AUDIT_PAGE_SIZE = 50
SGP_CLIENT_IP_HEADER = env_str("SGP_CLIENT_IP_HEADER", "HTTP_X_REAL_IP")
ACCESS_REQUEST_INSTRUCTIONS = env_str(
    "ACCESS_REQUEST_INSTRUCTIONS",
    "Você entrou com a sua conta de rede, mas ainda não tem perfil no SGP-P&D. "
    "Descreva abaixo para que precisa do acesso (projeto, função e quem aprova). "
    "O Administrador do sistema registra o perfil depois da aprovação do Gestor de P&D "
    "ou, para o perfil Qualidade/Assuntos Regulatórios, da Garantia da Qualidade.",
)

# Projetos (feature 002): prefixo do código e perfis com acesso aos dados financeiros.
PROJECT_CODE_PREFIX = env_str("PROJECT_CODE_PREFIX", "PD")
FINANCIAL_DATA_PROFILES = env_list("FINANCIAL_DATA_PROFILES", "")

# Cadastros de apoio (feature 003)
# Padrão do código de lote; provisório até a Qualidade definir o padrão oficial.
LOT_CODE_PATTERN = env_str("LOT_CODE_PATTERN", r"^[A-Za-z0-9][A-Za-z0-9./-]*$")
# Tamanho máximo de cada arquivo anexado ou importado, em MB.
FILE_MAX_MB = env_int("FILE_MAX_MB", 20)
# Tipos aceitos nos anexos de documentos (só os de assinatura conhecida: pdf, png, jpeg).
FILE_DOCUMENT_TYPES = env_list("FILE_DOCUMENT_TYPES", "pdf,png,jpeg")
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

# Assinatura eletrônica (feature 005)
SIGNATURE_MAX_FAILURES = env_int("SIGNATURE_MAX_FAILURES", 3)
SIGNATURE_LOCK_MINUTES = env_int("SIGNATURE_LOCK_MINUTES", 15)
REVIEW_ALERT_DAYS = env_int("REVIEW_ALERT_DAYS", 5)

# Caderno de laboratório (feature 008): dias corridos para assinar uma entrada antes de ela
# aparecer como atrasada (esclarecimento provisório, ratificar com o Gestor de P&D).
NOTEBOOK_SIGN_DAYS = env_int("NOTEBOOK_SIGN_DAYS", 7)

# Painel e notificações (feature 010): SMTP interno por variáveis de ambiente; no
# desenvolvimento os e-mails vão para arquivos (EMAIL_BACKEND de arquivo).
EMAIL_BACKEND = env_str("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env_str("EMAIL_HOST", "localhost")
EMAIL_PORT = env_int("EMAIL_PORT", 25)
EMAIL_HOST_USER = env_str("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env_str("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", False)
EMAIL_TIMEOUT = 15
EMAIL_FILE_PATH = env_str("EMAIL_FILE_PATH", str(BASE_DIR / "var" / "emails"))
DEFAULT_FROM_EMAIL = env_str("DEFAULT_FROM_EMAIL", "SGP-P&D <sgp-pd@localhost>")
SITE_URL = env_str("SITE_URL", "https://localhost:8443")
NOTIFICATION_DIGEST_HOUR = env_int("NOTIFICATION_DIGEST_HOUR", 7)
DASHBOARD_CACHE_SECONDS = env_int("DASHBOARD_CACHE_SECONDS", 300)
CACHE_URL = env_str("CACHE_URL", "")
CACHES = {
    "default": (
        {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": CACHE_URL}
        if CACHE_URL
        else {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
    )
}

# Geração de documentos (feature 006): certificado do selo (PKCS#12) e senha só em variáveis de
# ambiente; sem certificado, o PDF oficial não é emitido.
DOCUMENT_SEAL_PKCS12 = env_str("DOCUMENT_SEAL_PKCS12", "")
DOCUMENT_SEAL_PASSWORD = env_str("DOCUMENT_SEAL_PASSWORD", "")
DOCUMENT_GENERATION_TIME_LIMIT = env_int("DOCUMENT_GENERATION_TIME_LIMIT", 120)

# Internacionalização: interface em português; datas gravadas em UTC, exibidas em Brasília.
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = False
DATE_FORMAT = "d/m/Y"
DATETIME_FORMAT = "d/m/Y H:i:s"
SHORT_DATETIME_FORMAT = "d/m/Y H:i"

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "var" / "media"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
if DEBUG:
    # Desenvolvimento: arquivos estáticos servidos direto das apps, sem collectstatic.
    STORAGES["staticfiles"] = {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}
    WHITENOISE_USE_FINDERS = True
    WHITENOISE_AUTOREFRESH = True
    STATIC_ROOT.mkdir(parents=True, exist_ok=True)

# Celery: fila no Redis, sem banco de resultados; agendamento embutido no worker.
CELERY_BROKER_URL = env_str("REDIS_URL", "redis://redis:6379/0")
CELERY_TASK_IGNORE_RESULT = True
CELERY_TIMEZONE = TIME_ZONE
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BEAT_SCHEDULE = {
    "verificacao-diaria-da-trilha": {
        "task": "sgp.audit.verify_chain_scheduled",
        "schedule": crontab(hour=AUDIT_VERIFY_HOUR, minute=AUDIT_VERIFY_MINUTE),
    },
    # Feature 013: registra a entrada em vigência das versões de modelo com data futura.
    "vigencia-diaria-dos-modelos": {
        "task": "sgp.revisions.record_due",
        "schedule": crontab(hour=0, minute=5),
    },
    # Feature 010: resumo diário das pendências vencidas.
    "resumo-diario-de-pendencias": {
        "task": "sgp.notifications.daily_digest",
        "schedule": crontab(hour=NOTIFICATION_DIGEST_HOUR, minute=0),
    },
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "padrao": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "padrao"},
    },
    "root": {"handlers": ["console"], "level": env_str("LOG_LEVEL", "INFO")},
    "loggers": {
        "django_auth_ldap": {"level": env_str("LDAP_LOG_LEVEL", "WARNING")},
        # Geração de documentos (feature 006): só avisos e erros do WeasyPrint e do fontTools.
        "weasyprint": {"level": "WARNING"},
        "fontTools": {"level": "WARNING"},
    },
}
