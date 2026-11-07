"""Amostras sem dados pessoais de pacientes (US4: FR-015, FR-016, SC-003 da feature 003)."""

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from sgp.accounts.profiles import Profile
from sgp.catalog import lgpd
from sgp.catalog.models import Sample
from sgp.vocab.models import get_term

pytestmark = [pytest.mark.django_db]


@pytest.mark.req("003:FR-015")
@pytest.mark.parametrize(
    "identifier", ["AM-001", "S1", "2026/045", "LOTE.7-A", "AM_01", "a1", "X" * 29 + "1"]
)
def test_identificadores_internos_aceitos(identifier):
    lgpd.validate_identifier(identifier)


@pytest.mark.req("003:FR-015")
@pytest.mark.req("003:SC-003")
@pytest.mark.parametrize(
    "identifier",
    ["Maria Silva", "MariaSilva", "joao.souza", "AM 001", "-AM1", "A" * 30 + "1", ""],
)
def test_identificadores_recusados(identifier):
    with pytest.raises(ValidationError, match="código interno"):
        lgpd.validate_identifier(identifier)


@pytest.mark.req("003:FR-016")
@pytest.mark.req("003:SC-003")
@pytest.mark.parametrize(
    "text,finding",
    [
        ("Doador 123.456.789-09", "CPF"),
        ("cpf 12345678909", "CPF"),
        ("contato fulano@exemplo.com.br", "e-mail"),
        ("ligar (31) 99999-8888", "telefone"),
        ("tel 31 3333-4444", "telefone"),
        ("+55 11 91234-5678", "telefone"),
        ("Paciente internado", "identificação de paciente"),
        ("amostra de pacientes do ambulatório", "identificação de paciente"),
        ("Nome: J. S.", "identificação de paciente"),
    ],
)
def test_textos_com_dados_pessoais_sao_recusados(text, finding):
    assert finding in lgpd.personal_data_findings(text)
    with pytest.raises(ValidationError, match="LGPD"):
        lgpd.validate_no_personal_data(text)


@pytest.mark.req("003:FR-016")
@pytest.mark.parametrize(
    "text",
    [
        "Reagente; concentração 12 U/mL",
        "Ct 28,5; carga viral 1.000 cópias/mL",
        "Banco de amostras interno, lote 2025-0312",
        "Positivo para o analito; status: caracterizada",
        "Nomenclatura do fabricante",
    ],
)
def test_textos_analiticos_passam(text):
    assert lgpd.personal_data_findings(text) == []


def sample_post(**overrides):
    data = {
        "identifier": "AM-100",
        "sample_type": get_term("tipo-amostra", "soro").pk,
        "origin": "Banco de amostras interno",
        "characterization": "Reagente; 12 U/mL",
        "storage": get_term("armazenamento", "2-8").pk,
        "storage_detail": "",
        "collection_date": "",
    }
    data.update(overrides)
    return data


@pytest.mark.req("003:SC-003")
@pytest.mark.parametrize(
    "field,value",
    [
        ("identifier", "Maria Silva"),
        ("origin", "Hospital X, paciente João"),
        ("characterization", "paciente João, CPF 123.456.789-00"),
        ("storage_detail", "Freezer do Dr. contato medico@hospital.org"),
    ],
)
def test_nenhum_campo_da_amostra_aceita_dado_de_paciente(
    client, login_as, vocab_seed, field, value
):
    login_as(Profile.ANALYST)
    response = client.post(reverse("catalog:new", args=["amostras"]), sample_post(**{field: value}))
    assert response.status_code == 200
    content = response.content.decode()
    assert "LGPD" in content or "código interno" in content
    assert not Sample.objects.exists()


@pytest.mark.req("003:FR-015")
def test_amostra_valida_e_cadastrada(client, login_as, vocab_seed):
    login_as(Profile.ANALYST)
    response = client.post(reverse("catalog:new", args=["amostras"]), sample_post())
    assert response.status_code == 302
    sample = Sample.objects.get()
    assert (sample.identifier, sample.sample_type.label, sample.storage.label) == (
        "AM-100",
        "Soro",
        "2 a 8 °C",
    )


@pytest.mark.req("003:FR-015")
def test_modelo_da_amostra_nao_tem_campo_de_paciente():
    names = {field.name for field in Sample._meta.get_fields()}
    for forbidden in ("patient", "patient_name", "cpf", "name", "birth_date", "email", "phone"):
        assert forbidden not in names
