"""Fixtures do dossiê técnico (feature 011). Dados fictícios criados só para os testes."""

import io

import pytest

from tests.catalog.conftest import PDF_BYTES  # noqa: F401
from tests.fulldoc.conftest import (  # noqa: F401
    create_sub,
    final_check_topics,
    force_approve,
    member,
    signed_project,
)
from tests.subdocuments.conftest import entry_topics, manager, standard  # noqa: F401

MINIMAL = """
itens:
  - numero: I
    titulo: DESCRIÇÃO DO PRODUTO
    subitens:
      - {numero: A, titulo: Funcionalidade, fontes: [{tipo: subdocumento, subdocumento: entrada, topico: funcionalidade}]}
      - {numero: B, titulo: Analito, fontes: [{tipo: complemento}]}
  - numero: II
    titulo: GERENCIAMENTO DE RISCO
    fontes: [{tipo: anexos, subdocumento: entrada, topico: gerenciamento_risco}]
  - numero: III
    titulo: NORMAS TÉCNICAS
    fontes: [{tipo: normas}]
  - numero: IV
    titulo: DESEMPENHO CLÍNICO
    classes: [III, IV]
    fora_da_classe: Exigido apenas para as classes III e IV.
    fontes: [{tipo: complemento}]
  - numero: V
    titulo: UNIDADE FABRIL
    fontes: [{tipo: texto_padrao, chave: unidade-fabril}]
"""


def pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    return " ".join(
        " ".join((page.extract_text() or "").split()) for page in PdfReader(io.BytesIO(data)).pages
    )


@pytest.fixture
def quality(make_user):
    from sgp.accounts.profiles import Profile

    return make_user(None, Profile.QUALITY)


@pytest.fixture
def company(quality):
    from sgp.dossier import services

    return services.save_company(
        by=quality,
        data={
            "legal_name": "Empresa Fictícia de Diagnósticos Ltda.",
            "city": "Cidade Fictícia",
            "rt_name": "Pessoa Responsável Fictícia",
            "rt_council": "Conselho Regional de Farmácia",
            "rt_uf": "mg",
            "rt_number": "00000",
            "rt_title": "Farmacêutica",
        },
    )


@pytest.fixture
def approved_entry_with_class(signed_project, create_sub, force_approve, standard, quality):
    """Entrada aprovada (classe informada) com norma e matriz de risco anexada."""
    from django.core.files.uploadedfile import SimpleUploadedFile

    from sgp.files.storage import store_upload
    from tests.catalog.conftest import PDF_BYTES as pdf_bytes

    def _approve(risk_class="II", project=None):
        project = project or signed_project
        matrix = store_upload(
            SimpleUploadedFile("matriz-risco.pdf", pdf_bytes, content_type="application/pdf"),
            by=quality,
        )
        topics = entry_topics(standard.pk)
        topics["classificacao_risco"]["values"]["classe"] = risk_class
        topics["gerenciamento_risco"]["values"]["matriz"] = [matrix.pk]
        sub = create_sub(project, "entrada")
        return force_approve(sub, topics)

    return _approve


@pytest.fixture
def minimal_definition(quality):
    from sgp.dossier import services

    return services.publish_definition(by=quality, text=MINIMAL, note="Definição mínima de teste")


@pytest.fixture
def approved_text(quality, manager, signing):
    from sgp.dossier import services

    def _approve(key="unidade-fabril", text="Unidade fabril fictícia com área limpa."):
        record = services.save_text(
            by=quality, key=key, title=key.replace("-", " ").title(), text=text
        )
        signing.enable(manager)
        return services.approve_text(record, by=manager, password=signing.password)

    return _approve
