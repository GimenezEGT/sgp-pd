"""Importação CSV/XLSX com mapeamento por equipamento (FR-006, SC-005)."""

import io
import time

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from sgp.studies import importing
from sgp.studies.models import ImportMapping

pytestmark = [pytest.mark.django_db]


def csv_file(text, name="medidas.csv"):
    return SimpleUploadedFile(name, text.encode("utf-8"), content_type="text/csv")


@pytest.mark.req("007:FR-006")
def test_csv_com_ponto_e_virgula_pre_visualizacao_e_confirmacao(make_study, analyst, events):
    study = make_study("linearidade")
    upload = csv_file("Conc;Leitura\n1;3,0\n2;5,0\n3;abc\n4;9,0\n")
    preview = importing.preview(study, upload, {"x": "Conc", "y": "Leitura"})
    assert (preview["total"], preview["accepted"]) == (4, 3)
    assert preview["errors"] and preview["errors"][0].startswith("Linha 3")
    count = importing.confirm(
        study,
        by=analyst,
        token=preview["token"],
        equipment="Leitor de teste",
        mapping={"x": "Conc", "y": "Leitura"},
    )
    study.refresh_from_db()
    assert count == 3 and len(study.rows) == 3
    assert ImportMapping.objects.get(equipment="Leitor de teste").mapping == {
        "x": "Conc",
        "y": "Leitura",
    }
    assert events("studies.imported") and events("studies.mapping_saved")


@pytest.mark.req("007:FR-006")
def test_xlsx_virgula_e_colunas_inexistentes(make_study, analyst):
    from openpyxl import Workbook

    study = make_study("repetibilidade")
    book = Workbook()
    book.active.append(["Valor"])
    for value in (10, 11, 12):
        book.active.append([value])
    buffer = io.BytesIO()
    book.save(buffer)
    upload = SimpleUploadedFile("medidas.xlsx", buffer.getvalue())
    preview = importing.preview(study, upload, {"y": "Valor"})
    assert preview["accepted"] == 3
    comma = importing.preview(study, csv_file("Valor,Outro\n1.5,x\n"), {"y": "Valor"})
    assert comma["accepted"] == 1
    with pytest.raises(ValidationError, match="Colunas não encontradas"):
        importing.preview(study, csv_file("A;B\n1;2\n"), {"y": "Valor"})
    with pytest.raises(ValidationError, match="CSV ou XLSX"):
        importing.preview(study, SimpleUploadedFile("x.txt", b"1"), {"y": "Valor"})


@pytest.mark.req("007:FR-006")
def test_token_adulterado_ou_de_outro_estudo_e_recusado(make_study, analyst):
    study, other = make_study("repetibilidade"), make_study("repetibilidade", title="Outro")
    preview = importing.preview(study, csv_file("V\n1\n"), {"y": "V"})
    with pytest.raises(ValidationError):
        importing.confirm(study, by=analyst, token=preview["token"] + "x", equipment="", mapping={})
    with pytest.raises(ValidationError, match="outro estudo"):
        importing.confirm(other, by=analyst, token=preview["token"], equipment="", mapping={})


@pytest.mark.req("007:SC-005")
def test_pre_visualizacao_de_1000_linhas_em_menos_de_10_segundos(make_study):
    study = make_study("repetibilidade")
    text = "Valor\n" + "\n".join(f"{100 + i % 7},{i % 10}" for i in range(1000))
    start = time.perf_counter()
    preview = importing.preview(study, csv_file(text), {"y": "Valor"})
    assert preview["accepted"] == 1000 and time.perf_counter() - start < 10


@pytest.mark.req("007:FR-006")
def test_tela_de_importacao(make_study, analyst, client):
    study = make_study("repetibilidade")
    client.force_login(analyst)
    url = reverse("studies:import", args=[study.pk])
    page = client.post(
        url, {"equipamento": "Leitor A", "col__y": "Valor", "arquivo": csv_file("Valor\n1\n2\n")}
    )
    text = page.content.decode()
    assert "2 aceita(s)" in text
    token = page.context["preview"]["token"]
    client.post(
        url, {"acao": "confirmar", "token": token, "equipamento": "Leitor A", "col__y": "Valor"}
    )
    study.refresh_from_db()
    assert len(study.rows) == 2
