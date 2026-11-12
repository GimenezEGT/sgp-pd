"""Fixtures da geração de documentos (feature 006). Dados fictícios criados só para os testes."""

import datetime
import io

import pytest

from tests.catalog.conftest import lot_data, make_lot, make_material  # noqa: F401
from tests.subdocuments.conftest import (  # noqa: F401
    analyst,
    approve_quick,
    approved_entry,
    entry_topics,
    make_subdocument,
    manager,
    project,
    standard,
)

SEAL_PASSWORD = "selo-de-teste"


@pytest.fixture
def quality(make_user):
    from sgp.accounts.profiles import Profile

    return make_user(None, Profile.QUALITY)


@pytest.fixture
def seal_cert(settings, tmp_path):
    """Certificado autoassinado de teste para o selo; devolve a raiz de confiança (asn1crypto)."""
    from asn1crypto import x509 as asn1_x509
    from cryptography.hazmat.primitives import serialization

    from sgp.documents.testcert import write_pkcs12

    path = tmp_path / "selo-teste.p12"
    certificate = write_pkcs12(
        path,
        SEAL_PASSWORD.encode(),
        common_name="Selo de TESTE automatizado",
        valid_days=30,
        now=datetime.datetime.now(datetime.UTC),
    )
    settings.DOCUMENT_SEAL_PKCS12 = str(path)
    settings.DOCUMENT_SEAL_PASSWORD = SEAL_PASSWORD
    return asn1_x509.Certificate.load(certificate.public_bytes(serialization.Encoding.DER))


@pytest.fixture
def generate():
    """Pede e executa a geração como o worker faria (sem esperar o commit da transação)."""
    from sgp.documents import services
    from sgp.documents.models import GenerationRequest

    def _generate(kind, obj, fmt, by):
        pending = services.request_generation(kind, obj, fmt, by=by)
        services.run_request(pending.pk)
        return GenerationRequest.objects.select_related("result__file").get(pk=pending.pk)

    return _generate


@pytest.fixture
def file_bytes():
    from sgp.files.storage import read_verified

    def _bytes(generated):
        return read_verified(generated.file)

    return _bytes


def pdf_pages(data: bytes) -> list[str]:
    from pypdf import PdfReader

    return [page.extract_text() or "" for page in PdfReader(io.BytesIO(data)).pages]


def flat(text: str) -> str:
    return " ".join(text.split())


@pytest.fixture
def complete_entry(project, analyst, standard, make_subdocument):
    """Entrada de Projeto completa, em rascunho."""
    from sgp.subdocuments import services

    entry = make_subdocument(project, "entrada")
    return services.save_subdocument(entry, by=analyst, data={"topics": entry_topics(standard.pk)})
