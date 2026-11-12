"""Fixtures do documento completo (feature 009). Dados fictícios criados só para os testes."""

import io

import pytest

from tests.documents.conftest import seal_cert  # noqa: F401
from tests.subdocuments.conftest import manager  # noqa: F401

FLOW = (
    "entrada",
    "formulacao",
    "lote-piloto",
    "rapd",
    "analise-critica",
    "validacao",
    "verificacao-final",
    "saida",
)


def pdf_text(data: bytes) -> list[str]:
    from pypdf import PdfReader

    return [page.extract_text() or "" for page in PdfReader(io.BytesIO(data)).pages]


def outline(data: bytes) -> list[tuple[str, int]]:
    """(título, página) dos marcadores de primeiro nível do PDF."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    items = []
    for item in reader.outline:
        if isinstance(item, list):
            continue
        items.append((item.title, reader.get_destination_page_number(item) + 1))
    return items


@pytest.fixture
def signed_project(make_project, fill_project, manager, signing):
    """Projeto aprovado pela assinatura da 005: TAP e Plano de Negócios congelados (006)."""
    from sgp.signatures import services as signatures

    project = fill_project(make_project(title="Kit para o documento completo"))
    signing.enable(project.leader, manager)
    signatures.submit_project(project, by=project.leader, password=signing.password)
    signatures.approve_project(project, by=manager, password=signing.password)
    project.refresh_from_db()
    return project


@pytest.fixture
def member(signed_project, make_user):
    from sgp.accounts.profiles import Profile
    from sgp.projects import services

    user = make_user(None, Profile.ANALYST)
    services.add_member(signed_project, by=signed_project.leader, user=user, role="Analista")
    return user


@pytest.fixture
def force_approve(manager):
    """Aprova sem a completude do formulário: versão aprovada, assinatura e conteúdo congelado."""
    from django.utils import timezone

    from sgp.documents import content
    from sgp.signatures.canonical import content_hash
    from sgp.signatures.models import ApprovedVersion, Meaning, Signature
    from sgp.subdocuments.models import Subdocument, SubdocumentStatus

    def _approve(sub, topics=None):
        if topics is not None:
            Subdocument.objects.filter(pk=sub.pk).update(data={"topics": topics})
        Subdocument.objects.filter(pk=sub.pk).update(
            status=SubdocumentStatus.APPROVED, approved_by=manager, approved_at=timezone.now()
        )
        sub.refresh_from_db()
        data = {"modelo": {"id": sub.template_id}, "topicos": (sub.data or {}).get("topics", {})}
        digest = content_hash(data)
        approved = ApprovedVersion.objects.create(
            kind="subdocument",
            object_id=sub.pk,
            project=sub.project,
            version=sub.version,
            content=data,
            content_hash=digest,
            approved_by=manager,
        )
        Signature.objects.create(
            kind="subdocument",
            object_id=sub.pk,
            project=sub.project,
            version=sub.version,
            content_hash=digest,
            meaning=Meaning.APPROVED,
            signer=manager,
            signer_name=manager.get_full_name(),
            signer_title="Gestor de P&D",
        )
        content.freeze("subdocument", sub, approved=approved)
        return sub

    return _approve


@pytest.fixture
def create_sub(member):
    from sgp.subdocuments import services
    from sgp.vocab.models import get_term

    def _create(project, code):
        return services.create_subdocument(project, get_term("tipo-subdocumento", code), by=member)

    return _create


@pytest.fixture
def final_check_topics():
    """Tópicos da Verificação Final com um item reprovado (justificado) e os demais aprovados."""

    def _topics(sub, rejected=True):
        for topic in sub.template.topics:
            for field in topic["fields"]:
                if field["type"] == "derived_table" and field.get("source") == "entry_topics":
                    justify = field["justify_unless"]
                    rows = [
                        {"label": "Amostras", "values": {justify["column"]: justify["value"]}},
                        {
                            "label": "Funcionalidade",
                            "values": {
                                justify["column"]: "reprovado" if rejected else justify["value"],
                                justify["justification"]: "Fora do critério combinado",
                            },
                        },
                    ]
                    return {
                        topic["key"]: {
                            "na": False,
                            "justification": "",
                            "values": {field["key"]: {"rows": rows}},
                        }
                    }
        raise AssertionError("modelo da Verificação Final sem a lista de verificação")

    return _topics


@pytest.fixture
def complete_project(signed_project, create_sub, force_approve, final_check_topics):
    """Projeto com todos os subdocumentos do fluxo aprovados e congelados."""

    def _complete(rejected=False):
        for code in FLOW:
            sub = create_sub(signed_project, code)
            topics = (
                final_check_topics(sub, rejected=rejected) if code == "verificacao-final" else None
            )
            force_approve(sub, topics)
        return signed_project

    return _complete


@pytest.fixture
def run_fulldoc():
    """Pede e executa como o worker faria (sem esperar o commit da transação do teste)."""
    from sgp.fulldoc import services
    from sgp.fulldoc.models import FullDocumentRequest

    def _run(project, by, **options):
        pending = services.request_document(project, by=by, options=options)
        services.run_request(pending.pk)
        return FullDocumentRequest.objects.select_related("result__file").get(pk=pending.pk)

    return _run


@pytest.fixture
def document_bytes():
    from sgp.files.storage import read_verified

    def _bytes(document):
        return read_verified(document.file)

    return _bytes
