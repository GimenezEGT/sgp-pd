"""Fixtures dos cadastros de apoio (feature 003). Dados fictícios criados só para os testes."""

from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

PDF_BYTES = b"%PDF-1.4\n% certificado de teste\n1 0 obj << >> endobj\ntrailer << >>\n%%EOF\n"


@pytest.fixture
def pdf_file():
    def _make(name="certificado.pdf", content=PDF_BYTES):
        return SimpleUploadedFile(name, content, content_type="application/pdf")

    return _make


@pytest.fixture
def quality_user(make_user):
    from sgp.accounts.profiles import Profile

    return make_user(None, Profile.QUALITY)


@pytest.fixture
def analyst(make_user):
    from sgp.accounts.profiles import Profile

    return make_user(None, Profile.ANALYST)


@pytest.fixture
def member_of():
    """Inclui a pessoa na equipe do projeto aberto (acesso pela regra única)."""
    from sgp.projects import services

    def _add(project, user):
        services.add_member(project, by=project.leader, user=user, role="Analista do projeto")
        return user

    return _add


@pytest.fixture
def lot_data():
    def _data(project, responsible, **overrides):
        data = {
            "project": project,
            "code": "LP-001",
            "lot_type": "pilot",
            "manufacture_date": date(2026, 9, 1),
            "expiry_date": date(2027, 9, 1),
            "manufacturing_site": "Planta piloto",
            "production_responsible": responsible,
        }
        data.update(overrides)
        return data

    return _data


@pytest.fixture
def make_lot(lot_data):
    from sgp.catalog import versioning
    from sgp.catalog.kinds import LOTS

    def _make(project, by, **overrides):
        return versioning.create_record(LOTS, by=by, data=lot_data(project, by, **overrides))

    return _make


@pytest.fixture
def make_material(db):
    from sgp.catalog import versioning
    from sgp.catalog.kinds import MATERIALS

    counter = {"value": 0}

    def _make(by, **overrides):
        counter["value"] += 1
        data = {
            "code": f"MP-{counter['value']:04d}",
            "description": "Tampão de teste",
            "material_type": "raw",
            "manufacturer": "Fornecedor fictício",
            "manufacturer_lot": "F-100",
            "new_to_company": False,
        }
        data.update(overrides)
        return versioning.create_record(MATERIALS, by=by, data=data)

    return _make


@pytest.fixture
def make_sample(vocab_seed):
    from sgp.catalog import versioning
    from sgp.catalog.kinds import SAMPLES
    from sgp.vocab.models import get_term

    counter = {"value": 0}

    def _make(by, **overrides):
        counter["value"] += 1
        data = {
            "identifier": f"AM-{counter['value']:04d}",
            "sample_type": get_term("tipo-amostra", "soro"),
            "origin": "Banco de amostras interno",
            "characterization": "Reagente; concentração 12 U/mL",
            "storage": get_term("armazenamento", "menos-20"),
            "storage_detail": "",
            "collection_date": None,
        }
        data.update(overrides)
        return versioning.create_record(SAMPLES, by=by, data=data)

    return _make
