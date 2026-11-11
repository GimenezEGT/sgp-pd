"""PDF oficial: assinaturas, selo, código de verificação e consulta (FR-012 a FR-015, SC-003)."""

import datetime

import pytest
from django.urls import reverse

from sgp.accounts.profiles import Profile
from sgp.documents import seal, services
from sgp.documents.models import GeneratedDocument
from tests.documents.conftest import flat, pdf_pages

pytestmark = [pytest.mark.django_db]


@pytest.mark.req("006:FR-012")
@pytest.mark.req("006:SC-003")
def test_pdf_oficial_selado_e_alteracao_de_um_byte_acusada(
    approved_entry, analyst, generate, file_bytes, seal_cert
):
    pending = generate("subdocument", approved_entry, "pdf", analyst)
    assert pending.status == "done" and pending.official is True
    data = file_bytes(pending.result)
    assert seal.validate(data, [seal_cert]) == {"intact": True, "valid": True, "trusted": True}
    position = len(data) // 3
    tampered = data[:position] + bytes([(data[position] + 1) % 256]) + data[position + 1 :]
    assert seal.validate(tampered, [seal_cert])["intact"] is False


@pytest.mark.req("006:FR-012")
def test_bloco_de_assinaturas_data_e_relacao_final(
    approved_entry, analyst, manager, generate, file_bytes, seal_cert
):
    data = file_bytes(generate("subdocument", approved_entry, "pdf", analyst).result)
    pages = [flat(page) for page in pdf_pages(data)]
    cover = pages[0]
    assert (
        "assinatura eletrônica (Elaborado)" in cover and "assinatura eletrônica (Aprovado)" in cover
    )
    assert analyst.full_name in cover and manager.full_name in cover
    approved_on = approved_entry.approved_at.astimezone().strftime("%d/%m/%Y")
    assert f"Data: {approved_on}" in cover
    assert "RASCUNHO" not in " ".join(pages)
    last = pages[-1]
    assert "Registro de assinaturas eletrônicas" in last and "Resumo do conteúdo aprovado" in last


@pytest.mark.req("006:FR-012")
def test_aprovacao_por_delegacao_aparece_no_documento(
    complete_entry, analyst, manager, make_user, signing, generate, file_bytes, seal_cert
):
    from sgp.signatures import services as signatures

    delegate = make_user(None, Profile.PROJECT_LEADER)
    signatures.create_delegation(
        by=manager,
        delegate=delegate,
        starts_on=datetime.date.today(),
        ends_on=datetime.date.today() + datetime.timedelta(days=5),
        reason="Férias",
    )
    from sgp.projects import services as projects

    projects.add_member(
        complete_entry.project, by=complete_entry.project.leader, user=delegate, role="Apoio"
    )
    signing.submit("subdocument", complete_entry, analyst)
    signing.approve("subdocument", complete_entry, delegate)
    text = " ".join(
        flat(p)
        for p in pdf_pages(
            file_bytes(generate("subdocument", complete_entry, "pdf", analyst).result)
        )
    )
    assert "em delegação de" in text and manager.full_name in text


@pytest.mark.req("006:FR-013")
@pytest.mark.parametrize("problem", ["ausente", "vencido"])
def test_sem_certificado_valido_nao_sai_pdf_oficial(
    approved_entry, analyst, generate, settings, tmp_path, problem, events
):
    if problem == "ausente":
        settings.DOCUMENT_SEAL_PKCS12 = ""
    else:
        from sgp.documents.testcert import write_pkcs12

        path = tmp_path / "vencido.p12"
        write_pkcs12(
            path,
            b"senha",
            common_name="Vencido",
            valid_days=1,
            now=datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=30),
        )
        settings.DOCUMENT_SEAL_PKCS12, settings.DOCUMENT_SEAL_PASSWORD = str(path), "senha"
    pending = generate("subdocument", approved_entry, "pdf", analyst)
    assert pending.status == "failed" and "certificado do selo" in pending.error
    assert GeneratedDocument.objects.count() == 0
    assert events("documents.generation_failed")


@pytest.mark.req("006:FR-014")
def test_codigo_de_verificacao_estavel_e_consultavel(
    approved_entry, analyst, generate, file_bytes, seal_cert, client, make_user, events
):
    first = generate("subdocument", approved_entry, "pdf", analyst).result
    second = generate("subdocument", approved_entry, "pdf", analyst).result
    code = first.verification_code
    assert len(code) == 19 and code == second.verification_code
    assert f"Código de verificação: {code}" in flat(pdf_pages(file_bytes(first))[0])
    client.force_login(analyst)
    page = client.get(reverse("documents:verify"), {"codigo": code.lower().replace("-", "")})
    text = page.content.decode()
    assert "Código válido" in text and "Vigente" in text and first.file_hash in text
    assert reverse("documents:download", args=[first.pk]) in text
    outsider = make_user(None, Profile.ANALYST)
    client.force_login(outsider)
    text = client.get(reverse("documents:verify"), {"codigo": code}).content.decode()
    assert "Código válido" in text and "não tem acesso ao projeto" in text
    assert reverse("documents:download", args=[first.pk]) not in text
    assert approved_entry.project.code not in text
    text = client.get(
        reverse("documents:verify"), {"codigo": "ZZZZ-ZZZZ-ZZZZ-ZZZZ"}
    ).content.decode()
    assert "Código não encontrado" in text
    lookups = events("documents.verification_lookup")
    assert [e.new_value["encontrado"] for e in lookups] == [True, True, False]
    assert [e.new_value["com_acesso"] for e in lookups] == [True, False, False]


@pytest.mark.req("006:FR-014")
def test_versao_substituida_aparece_na_consulta(
    approved_entry, analyst, manager, generate, seal_cert, signing
):
    from sgp.signatures import services as signatures

    code = generate("subdocument", approved_entry, "pdf", analyst).result.verification_code
    signatures.new_version("subdocument", approved_entry, by=analyst, reason="Correção")
    signing.submit_and_approve("subdocument", approved_entry, analyst, manager)
    result = services.lookup(code, user=analyst)
    assert result["found"] and result["situation"] == "Substituída pela versão 02"


@pytest.mark.req("006:FR-015")
def test_docx_da_versao_aprovada_nao_tem_selo_nem_codigo(approved_entry, analyst, generate):
    doc = generate("subdocument", approved_entry, "docx", analyst).result
    assert doc.official is False and doc.verification_code == ""


@pytest.mark.req("006:FR-014")
def test_normalizacao_do_codigo():
    assert services.normalize_code("abcd efgh jkmn pqrs") == "ABCD-EFGH-JKMN-PQRS"
    assert services.normalize_code("ABCD-EFGH-JKMN-PQRO") == "ABCD-EFGH-JKMN-PQR0"
    assert services.normalize_code("curto") == ""


@pytest.mark.req("006:FR-013")
def test_certificado_de_teste_so_em_desenvolvimento(settings, tmp_path):
    from django.core.management import CommandError, call_command

    settings.DOCUMENT_SEAL_PKCS12 = str(tmp_path / "certs" / "selo.p12")
    settings.DOCUMENT_SEAL_PASSWORD = "senha-dev"
    settings.DEBUG = False
    with pytest.raises(CommandError, match="só em desenvolvimento"):
        call_command("selo_teste")
    settings.DEBUG = True
    call_command("selo_teste")
    assert (tmp_path / "certs" / "selo.p12").exists()
    assert seal.load_signer().signing_cert.subject.human_friendly
    call_command("selo_teste")  # já existe: não substitui sem --forcar
    settings.DOCUMENT_SEAL_PASSWORD = ""
    with pytest.raises(CommandError, match="Defina"):
        call_command("selo_teste", "--forcar")
