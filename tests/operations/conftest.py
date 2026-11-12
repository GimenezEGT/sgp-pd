"""Fixtures da feature 014 (cópia, restauração e qualificação). Dados fictícios."""

import pytest

from tests.documents.conftest import seal_cert  # noqa: F401


@pytest.fixture
def backup_dir(settings, tmp_path):
    """Destino de cópias temporário, irmão (e não filho) do MEDIA_ROOT dos testes."""
    target = tmp_path / "destino-copias"
    target.mkdir()
    settings.BACKUP_DIR = str(target)
    return target


@pytest.fixture
def it_admin(make_user):
    from sgp.accounts.profiles import Profile

    return make_user("ti.admin", Profile.ADMIN, email="ti@teste.local")


@pytest.fixture
def quality(make_user):
    from sgp.accounts.profiles import Profile

    return make_user("qualidade.teste", Profile.QUALITY, email="qa@teste.local")


@pytest.fixture
def analyst(make_user):
    from sgp.accounts.profiles import Profile

    return make_user("analista.teste", Profile.ANALYST)


@pytest.fixture
def stored_files(it_admin):
    from sgp.files.storage import store_bytes

    def _make(count=2, start=0):
        return [
            store_bytes(
                f"%PDF-1.4\n% arquivo fictício {index}\n".encode(),
                name=f"ficticio-{index}.pdf",
                kind="pdf",
                by=it_admin,
            )
            for index in range(start, start + count)
        ]

    return _make


@pytest.fixture
def live_counts():
    from django.db import connection

    from sgp.operations.backup import table_counts

    def _counts():
        with connection.cursor() as cursor:
            return table_counts(cursor)

    return _counts


@pytest.fixture
def restore_db_exists():
    from sgp.operations.backup import owner_connect
    from sgp.operations.restore import restore_db_name

    def _exists():
        with owner_connect(autocommit=True) as conn:
            return (
                conn.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s", [restore_db_name()]
                ).fetchone()
                is not None
            )

    return _exists
