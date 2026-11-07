"""Fixtures comuns e plugin de rastreabilidade requisito → teste (princípio VIII)."""

import json
import re
from pathlib import Path

import pytest
from django.core.management import call_command

from tests import fake_backend

REQ_PATTERN = re.compile(r"^\d{3}:(FR|SC)-\d{3}$")


def pytest_addoption(parser):
    parser.addoption(
        "--req-report",
        action="store",
        default=None,
        help="grava em JSON o mapa teste → requisitos (matriz de rastreabilidade)",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    report = {}
    for item in items:
        ids = []
        for marker in item.iter_markers("req"):
            for value in marker.args:
                if not REQ_PATTERN.match(value):
                    raise pytest.UsageError(f"Requisito inválido em {item.nodeid}: {value!r}")
                ids.append(value)
        report[item.nodeid] = sorted(set(ids))
    path = config.getoption("--req-report")
    if path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("apply_db_privileges", "--if-role-exists", verbosity=0)


@pytest.fixture(autouse=True)
def _reset_directory():
    fake_backend.reset()
    yield
    fake_backend.reset()


@pytest.fixture
def directory():
    return fake_backend


@pytest.fixture
def make_user(db):
    from sgp.accounts.models import ProfileAssignment, User

    counter = {"value": 0}

    def _make(username=None, *profiles, **attrs):
        counter["value"] += 1
        username = username or f"pessoa{counter['value']}"
        attrs.setdefault("full_name", f"Pessoa {username}")
        attrs.setdefault("job_title", "Analista de P&D")
        user = User.objects.create_user(username, **attrs)
        for profile in profiles:
            ProfileAssignment.objects.create(
                user=user,
                profile=profile,
                grant_reason="Preparação do teste",
                approval_reference="teste automatizado",
            )
        return user

    return _make


@pytest.fixture
def login_as(client, make_user):
    def _login(*profiles, username=None):
        user = make_user(username, *profiles)
        client.force_login(user)
        return user

    return _login


@pytest.fixture
def events():
    """Consulta rápida de eventos por tipo."""
    from sgp.audit.models import AuditEvent

    def _events(event_type=None):
        queryset = AuditEvent.objects.order_by("seq")
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        return list(queryset)

    return _events
