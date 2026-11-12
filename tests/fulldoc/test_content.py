"""Quadro de versões, trilha, caderno, histórico de versões, dados financeiros e anexos."""

import pytest
from django.utils import timezone

from sgp.fulldoc import compose
from sgp.notebook import services as notebook
from sgp.subdocuments.models import Subdocument
from tests.notebook.conftest import png_file

from .conftest import outline, pdf_text


def _flat(pages) -> str:
    return " ".join(" ".join(pages).split())


@pytest.mark.req("009:FR-008")
@pytest.mark.req("009:FR-010")
def test_quadro_de_versoes_e_historico_completo(
    complete_project, force_approve, run_fulldoc, document_bytes, seal_cert
):
    project = complete_project()
    entry = Subdocument.objects.get(project=project, subdocument_type__code="entrada")
    Subdocument.objects.filter(pk=entry.pk).update(version=2)
    entry.refresh_from_db()
    force_approve(entry)
    documents = compose.documents_in_order(project)
    rows = [
        row for row in compose.version_rows(documents) if row["document"] == "Entrada de Projeto"
    ]
    assert [(r["version"], r["situation"]) for r in rows] == [
        ("01", "Substituída"),
        ("02", "Vigente"),
    ]
    assert rows[0]["signers"] and "Aprovado" in rows[0]["signers"][0]
    current = document_bytes(run_fulldoc(project, project.leader).result)
    titles = [title for title, _ in outline(current)]
    assert sum(t.startswith("Entrada de Projeto") for t in titles) == 1
    full = document_bytes(run_fulldoc(project, project.leader, historico_versoes=True).result)
    titles = [title for title, _ in outline(full)]
    assert any("versão 01 (substituída)" in t for t in titles)
    assert "Versão substituída – aprovada em" in _flat(pdf_text(full))


@pytest.mark.req("009:FR-009")
def test_resumo_da_trilha_por_tipo_e_eventos_chave(signed_project):
    summary = compose.audit_summary(signed_project, timezone.now())
    labels = dict(summary["by_type"])
    assert summary["total"] == sum(labels.values()) and summary["first"] and summary["last"]
    assert labels.get("Projeto aprovado e aberto") == 1
    events = [row["event"] for row in summary["key_events"]]
    assert "Projeto aprovado e aberto" in events and "Documento aprovado com assinatura" in events
    assert all(row["who"] for row in summary["key_events"])


@pytest.mark.req("009:FR-007")
def test_caderno_resumido_ou_completo_so_com_entradas_assinadas(
    signed_project, member, signing, run_fulldoc, document_bytes
):
    entry = notebook.create_entry(signed_project, by=member, data={"title": "Ensaio de bancada"})
    image = notebook.add_attachment(entry, by=member, uploaded=png_file(), inline=True)
    notebook.update_entry(
        entry,
        by=member,
        data={
            "procedure": f'<p>Procedimento detalhado</p><p><img src="/arquivos/{image.file_id}/" alt="foto"></p>',
            "conclusion": "Conclusão do ensaio",
        },
    )
    signing.enable(member)
    notebook.sign_entry(entry, by=member, password=signing.password)
    notebook.create_entry(signed_project, by=member, data={"title": "Entrada ainda aberta"})
    summary = compose.notebook(signed_project, "resumido")
    assert [item["title"] for item in summary] == ["Ensaio de bancada"]
    assert summary[0]["conclusion"] == "Conclusão do ensaio" and "texts" not in summary[0]
    full = compose.notebook(signed_project, "completo")
    procedure = full[0]["texts"][0]["html"]
    assert 'src="data:image/png;base64,' in procedure and "/arquivos/" not in procedure
    short = _flat(
        pdf_text(document_bytes(run_fulldoc(signed_project, signed_project.leader).result))
    )
    assert "Ensaio de bancada" in short and "Conclusão do ensaio" in short
    assert "Procedimento detalhado" not in short and "Entrada ainda aberta" not in short
    long = _flat(
        pdf_text(
            document_bytes(
                run_fulldoc(signed_project, signed_project.leader, caderno="completo").result
            )
        )
    )
    assert "Procedimento detalhado" in long


@pytest.mark.req("009:FR-005")
def test_plano_de_negocios_sem_os_campos_financeiros(signed_project, run_fulldoc, document_bytes):
    plan = next(
        part
        for part in compose.compose(
            signed_project,
            options={"caderno": "resumido"},
            with_financials=False,
            pending=[],
            until=timezone.now(),
        )["parts"]
        if part.get("doc_kind") == "business_plan"
    )
    masked = [
        s
        for s in plan["content"]["sections"]
        if s["blocks"] and s["blocks"][0].get("text") == compose.FINANCIAL_NOTE
    ]
    assert any(s["label"] == compose.RETURN_SECTION for s in masked)
    assert any("Custo" in s["label"] for s in masked)
    text = _flat(
        pdf_text(
            document_bytes(
                run_fulldoc(signed_project, signed_project.leader, omitir_financeiro=True).result
            )
        )
    )
    assert "Dado financeiro omitido (acesso restrito)" in text and "250.000,00" not in text


@pytest.mark.req("009:FR-011")
def test_lista_de_anexos_com_origem_e_resumo(
    signed_project, member, signing, run_fulldoc, document_bytes
):
    entry = notebook.create_entry(signed_project, by=member, data={"title": "Com anexo"})
    attachment = notebook.add_attachment(entry, by=member, uploaded=png_file("placa.png"))
    signing.enable(member)
    notebook.sign_entry(entry, by=member, password=signing.password)
    text = _flat(
        pdf_text(document_bytes(run_fulldoc(signed_project, signed_project.leader).result))
    )
    assert "placa.png" in text and "Caderno – entrada 1" in text
    assert attachment.file.sha256[:20] in text.replace(" ", "")
