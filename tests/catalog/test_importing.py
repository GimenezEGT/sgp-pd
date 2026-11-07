"""Importação de insumos por planilha (US3: FR-013, SC-002 da feature 003)."""

import csv
import io
import time

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from openpyxl import Workbook

from sgp.accounts.profiles import Profile
from sgp.catalog import importing
from sgp.catalog.models import ImportBatch, ImportStatus, Material

pytestmark = [pytest.mark.django_db]

HEADER = ["codigo", "descricao", "tipo", "fabricante", "lote_fabricante", "novo"]


def csv_upload(
    rows, *, header=HEADER, delimiter=";", encoding="utf-8", bom=False, name="insumos.csv"
):
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=delimiter, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    text = buffer.getvalue()
    content = text.encode(encoding)
    if bom:
        content = importing.UTF8_BOM.encode("utf-8") + content
    return SimpleUploadedFile(name, content, content_type="text/csv")


def xlsx_upload(rows, header=HEADER):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(header)
    for row in rows:
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return SimpleUploadedFile("insumos.xlsx", buffer.getvalue())


@pytest.fixture
def editor(make_user):
    return make_user(None, Profile.ANALYST)


VALID = [
    ["MP-1", "Cloreto de sódio", "matéria-prima", "Fornecedor A", "L1", "sim"],
    ["ME-1", "Frasco 10 mL", "material de embalagem", "Fornecedor B", "", "não"],
]


@pytest.mark.req("003:FR-013")
@pytest.mark.parametrize(
    "upload",
    [
        lambda: csv_upload(VALID),
        lambda: csv_upload(VALID, delimiter=","),
        lambda: csv_upload(VALID, bom=True),
        lambda: csv_upload(VALID, encoding="latin-1"),
        lambda: xlsx_upload(VALID),
    ],
    ids=["csv-ponto-e-virgula", "csv-virgula", "utf8-bom", "latin1", "xlsx"],
)
def test_formatos_aceitos(editor, upload):
    batch = importing.preview(upload(), by=editor)
    assert (batch.valid_count, batch.rejected_count) == (2, 0)
    first = batch.rows[0]["dados"]
    assert first == {
        "codigo": "MP-1",
        "descricao": "Cloreto de sódio",
        "tipo": "raw",
        "fabricante": "Fornecedor A",
        "lote_fabricante": "L1",
        "novo": True,
    }
    assert batch.rows[1]["dados"]["tipo"] == "packaging"


@pytest.mark.req("003:FR-013")
def test_cabecalho_sem_acento_e_sem_caixa(editor):
    header = ["Código", "Descrição", "TIPO", "Fabricante", "Lote fabricante", "Novo"]
    batch = importing.preview(csv_upload(VALID, header=header), by=editor)
    assert batch.valid_count == 2
    assert batch.rows[0]["dados"]["lote_fabricante"] == "L1"


@pytest.mark.req("003:FR-013")
def test_coluna_obrigatoria_faltando_recusa_o_arquivo(editor):
    with pytest.raises(ValidationError) as error:
        importing.preview(csv_upload([["MP-1", "X"]], header=["codigo", "descricao"]), by=editor)
    message = error.value.messages[0]
    assert "faltam as colunas tipo" in message
    assert "codigo; descricao; tipo; fabricante; lote_fabricante; novo" in message
    assert not ImportBatch.objects.exists()


@pytest.mark.req("003:FR-013")
def test_motivos_de_rejeicao_linha_a_linha(editor, make_material):
    make_material(editor, code="MP-EXISTE")
    rows = [
        ["MP-1", "Válido", "MP", "", "", ""],
        ["MP-1", "Repetido na planilha", "MP", "", "", ""],
        ["MP-EXISTE", "Já cadastrado", "ME", "", "", ""],
        ["", "Sem código", "MP", "", "", ""],
        ["MP 2", "Com espaço", "MP", "", "", ""],
        ["MP-3", "", "MP", "", "", ""],
        ["MP-4", "Tipo errado", "reagente", "", "", ""],
        ["MP-5", "Novo inválido", "MP", "", "", "talvez"],
        ["MP-6", "D" * 301, "MP", "", "", ""],
    ]
    batch = importing.preview(csv_upload(rows), by=editor)
    errors = {row["linha"]: row["erros"] for row in batch.rows}
    assert errors[2] == []
    assert errors[3] == ["código repetido na planilha (linha 2)"]
    assert errors[4] == ["código já cadastrado"]
    assert errors[5] == ["código vazio"]
    assert errors[6] == ["código com espaços"]
    assert errors[7] == ["descrição vazia"]
    assert errors[8] == ["tipo inválido: 'reagente' (use matéria-prima ou material de embalagem)"]
    assert errors[9] == ["valor inválido em novo: 'talvez' (use sim ou não)"]
    assert errors[10] == ["descricao passa de 300 caracteres"]
    assert (batch.valid_count, batch.rejected_count) == (1, 8)


@pytest.mark.req("003:FR-013")
def test_pre_visualizacao_nao_cria_insumo(editor, events):
    batch = importing.preview(csv_upload(VALID), by=editor)
    assert batch.status == ImportStatus.PREVIEW
    assert not Material.objects.exists()
    event = events("catalog.import_previewed")[-1]
    assert event.new_value == {"arquivo": "insumos.csv", "linhas": 2, "validas": 2, "rejeitadas": 0}
    assert batch.source_file.sha256


@pytest.mark.req("003:FR-013")
def test_confirmacao_cria_so_as_validas_e_revalida(editor, make_material, events):
    rows = VALID + [["MP-ERR", "", "MP", "", "", ""]]
    batch = importing.preview(csv_upload(rows), by=editor)
    make_material(editor, code="ME-1")  # código ocupado entre a pré-visualização e a confirmação
    batch = importing.confirm(batch, by=editor)
    assert batch.status == ImportStatus.CONFIRMED
    assert set(Material.objects.values_list("code", flat=True)) == {"MP-1", "ME-1"}
    assert Material.objects.get(code="MP-1").new_to_company is True
    assert (batch.created_count, batch.rejected_count) == (1, 2)
    revalidated = next(row for row in batch.rows if row["dados"]["codigo"] == "ME-1")
    assert revalidated["erros"] == ["código cadastrado depois da pré-visualização"]
    assert events("catalog.import_confirmed")[-1].new_value == {"criados": 1, "rejeitadas": 2}
    with pytest.raises(ValidationError, match="já foi confirmada"):
        importing.confirm(batch, by=editor)


@pytest.mark.req("003:FR-013")
def test_relatorio_de_rejeicoes(editor):
    rows = VALID + [["MP-1", "Repetido", "MP", "", "", ""]]
    batch = importing.preview(csv_upload(rows), by=editor)
    report = importing.rejection_report(batch)
    assert report.startswith(importing.UTF8_BOM)
    lines = report[1:].split("\r\n")
    assert lines[0] == "linha;codigo;descricao;motivos"
    assert lines[1] == "4;MP-1;Repetido;código repetido na planilha (linha 2)"


@pytest.mark.req("003:FR-013")
def test_limite_de_linhas(editor, monkeypatch):
    monkeypatch.setattr(importing, "MAX_ROWS", 3)
    rows = [[f"MP-{i}", "Item", "MP", "", "", ""] for i in range(4)]
    with pytest.raises(ValidationError, match="o limite é 3 por arquivo"):
        importing.preview(csv_upload(rows), by=editor)


@pytest.mark.req("003:FR-013")
def test_fluxo_pelas_telas(client, login_as):
    login_as(Profile.ANALYST)
    template = client.get(reverse("catalog:import_template"))
    assert (
        template.content.decode("utf-8")
        .lstrip(importing.UTF8_BOM)
        .startswith("codigo;descricao;tipo;fabricante;lote_fabricante;novo")
    )
    rows = VALID + [["MP-1", "Repetido", "MP", "", "", ""]]
    response = client.post(reverse("catalog:import"), {"spreadsheet": csv_upload(rows)})
    batch = ImportBatch.objects.get()
    assert response["Location"] == reverse("catalog:import_batch", args=[batch.pk])
    preview = client.get(response["Location"]).content.decode()
    assert "Nada foi gravado no cadastro de insumos ainda" in preview
    assert "código repetido na planilha (linha 2)" in preview
    client.post(reverse("catalog:import_batch", args=[batch.pk]))
    assert Material.objects.count() == 2
    report = client.get(reverse("catalog:import_rejections", args=[batch.pk]))
    assert "rejeicoes-importacao" in report["Content-Disposition"]
    assert "4;MP-1;Repetido" in report.content.decode("utf-8")


@pytest.mark.req("003:FR-013")
def test_arquivo_fora_do_layout_pela_tela(client, login_as):
    login_as(Profile.ANALYST)
    response = client.post(
        reverse("catalog:import"),
        {"spreadsheet": csv_upload([["a", "b"]], header=["nome", "valor"])},
    )
    assert response.status_code == 200
    assert "A planilha não segue o layout" in response.content.decode()
    response = client.post(
        reverse("catalog:import"), {"spreadsheet": SimpleUploadedFile("insumos.pdf", b"%PDF-1.4")}
    )
    assert "Tipo de arquivo não aceito" in response.content.decode()


@pytest.mark.req("003:FR-013")
def test_pre_visualizacao_abandonada_fica_registrada(editor):
    batch = importing.preview(csv_upload(VALID), by=editor)
    batch.refresh_from_db()
    assert batch.status == ImportStatus.PREVIEW and batch.created_count == 0


@pytest.mark.req("003:SC-002")
def test_importacao_de_500_linhas_em_menos_de_30_segundos(editor):
    rows = [[f"MP-{i:04d}", f"Insumo {i}", "MP", "Fornecedor", "", ""] for i in range(480)]
    rows += [[f"MP-{i:04d}", "Repetido", "MP", "", "", ""] for i in range(10)]
    rows += [[f"X-{i}", "", "tipo errado", "", "", ""] for i in range(10)]
    start = time.monotonic()
    batch = importing.preview(csv_upload(rows), by=editor)
    batch = importing.confirm(batch, by=editor)
    elapsed = time.monotonic() - start
    assert batch.created_count == 480 and batch.rejected_count == 20
    assert Material.objects.count() == 480
    assert len(importing.rejection_report(batch).splitlines()) == 21
    assert elapsed < 30, f"importação levou {elapsed:.1f} s"
