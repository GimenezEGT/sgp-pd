"""Cliente do gateway: token, renovação, chamadas e erros (FR-001, FR-002)."""

import pytest

from sgp.integrations import payloads, sankhya


@pytest.mark.req("012:FR-001")
@pytest.mark.req("012:FR-002")
def test_token_com_client_credentials_e_x_token_reaproveitado(gateway):
    first = sankhya.token()
    assert first == "token-1" and sankhya.token() == "token-1" and gateway.tokens == 1
    form = gateway.forms[0]
    assert form["grant_type"] == ["client_credentials"] and form["client_id"] == [
        "cliente-ficticio"
    ]


@pytest.mark.req("012:FR-001")
def test_renova_o_token_quando_o_gateway_responde_401(gateway):
    sankhya.token()
    gateway.unauthorized = 1
    response = sankhya.call(payloads.save_record("ENTIDADE", "CHAVE", "k:1", {"CAMPO": "valor"}))
    assert response["status"] == "1" and gateway.tokens == 2
    assert gateway.records["ENTIDADE"]["k:1"] == {"CHAVE": "k:1", "CAMPO": "valor"}


@pytest.mark.req("012:FR-001")
def test_erros_do_gateway_sem_credenciais_na_mensagem(gateway, settings):
    gateway.fail = 1
    with pytest.raises(sankhya.SankhyaUnavailable) as down:
        sankhya.call(payloads.save_record("E", "CHAVE", "k", {}))
    with pytest.raises(sankhya.SankhyaError, match="Serviço não permitido"):
        sankhya.call({"serviceName": "Outro.servico", "requestBody": {"dataSet": {}}})
    for exc in (down.value,):
        assert "segredo" not in str(exc) and "token-" not in str(exc)
    settings.SANKHYA_X_TOKEN = "errado"
    from django.core.cache import cache

    cache.delete(sankhya.TOKEN_KEY)
    with pytest.raises(sankhya.SankhyaError, match="recusada"):
        sankhya.token()


@pytest.mark.req("012:FR-002")
def test_desligada_ou_sem_credenciais(settings):
    settings.SANKHYA_ENABLED = False
    assert not sankhya.configured()
    with pytest.raises(sankhya.SankhyaUnavailable):
        sankhya.token()


@pytest.mark.req("012:FR-001")
def test_corpo_e_leitura_de_loadrecords(gateway):
    gateway.products["MP-001"] = {
        "CODPROD": "MP-001",
        "DESCRPROD": "Matéria-prima fictícia",
        "CODVOL": "KG",
    }
    response = sankhya.call(
        payloads.load_records("PRODUTO", ["CODPROD", "DESCRPROD", "CODVOL"], "CODPROD", "MP-001")
    )
    assert payloads.rows(response) == [
        {"CODPROD": "MP-001", "DESCRPROD": "Matéria-prima fictícia", "CODVOL": "KG"}
    ]
