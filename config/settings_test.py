"""Configuração dos testes automatizados.

Usa o papel dono do banco (cria o banco de testes e simula adulterações) e um backend de
autenticação falso para as regras; os testes marcados `ldap` usam o LDAP de desenvolvimento.
"""

import os

os.environ.setdefault(
    "DJANGO_SECRET_KEY", "chave-somente-para-testes-automatizados-0000000000000000"
)

from .settings import *  # noqa: E402,F403
from .settings import DATABASES  # noqa: E402

DATABASES["default"]["USER"] = os.environ.get("DB_OWNER_USER", "sgp_owner")
DATABASES["default"]["PASSWORD"] = os.environ.get("DB_OWNER_PASSWORD", "")
DATABASES["default"]["CONN_MAX_AGE"] = 0

AUTHENTICATION_BACKENDS = ["tests.fake_backend.FakeNetworkBackend"]
LDAP_PROFILE_GROUPS = {}

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
STATIC_ROOT = BASE_DIR / "var" / "staticfiles-test"  # noqa: F405
STATIC_ROOT.mkdir(parents=True, exist_ok=True)
WHITENOISE_USE_FINDERS = True

SECURE_COOKIES = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
DEBUG = False

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"

LOGIN_MAX_FAILURES = 5
LOGIN_LOCKOUT_MINUTES = 15
SESSION_IDLE_TIMEOUT_MINUTES = 30
