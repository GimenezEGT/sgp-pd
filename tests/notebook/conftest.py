"""Fixtures do caderno de laboratório (feature 008). Dados fictícios criados só para os testes."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from tests.catalog.conftest import lot_data, make_lot, make_material, make_sample  # noqa: F401
from tests.studies.conftest import make_study, study_type  # noqa: F401
from tests.subdocuments.conftest import (  # noqa: F401
    analyst,
    approve_quick,
    make_subdocument,
    manager,
    project,
)

PNG = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]) + b"imagem ficticia de teste"


def png_file(name="foto.png"):
    return SimpleUploadedFile(name, PNG, content_type="image/png")


def csv_file(text="Valor\n1,0\n2,0\n3,0\n", name="dados.csv"):
    return SimpleUploadedFile(name, text.encode("utf-8"), content_type="text/csv")


@pytest.fixture
def quality(make_user):
    from sgp.accounts.profiles import Profile

    return make_user(None, Profile.QUALITY)


@pytest.fixture
def outsider(make_user):
    """Analista que não é membro do projeto."""
    from sgp.accounts.profiles import Profile

    return make_user(None, Profile.ANALYST)


@pytest.fixture
def colleague(project, make_user):
    """Outro analista membro do projeto."""
    from sgp.accounts.profiles import Profile
    from sgp.projects import services

    user = make_user(None, Profile.ANALYST)
    services.add_member(project, by=project.leader, user=user, role="Analista")
    return user


@pytest.fixture
def leader(project):
    return project.leader


@pytest.fixture
def make_entry(project, analyst):
    from sgp.notebook import services

    def _make(title="Teste de solubilidade do reagente", by=None, on=None, **data):
        return services.create_entry(on or project, by=by or analyst, data={"title": title, **data})

    return _make


@pytest.fixture
def signed_entry(make_entry, analyst, signing):
    """Entrada preenchida, relevante e assinada pelo autor."""
    from sgp.notebook import services

    def _signed(relevant=True, **data):
        entry = make_entry(relevant=relevant, **data)
        entry = services.update_entry(
            entry, by=analyst, data={"procedure": "Preparo da solução tampão", "conclusion": "Ok"}
        )
        signing.enable(analyst)
        services.sign_entry(entry, by=analyst, password=signing.password)
        entry.refresh_from_db()
        return entry

    return _signed
