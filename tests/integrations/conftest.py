"""Servidor simulado do API Gateway da Sankhya e fixtures da feature 012 (dados fictícios)."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import pytest

from tests.catalog.conftest import lot_data, make_lot  # noqa: F401
from tests.dashboard.conftest import submitted_entry  # noqa: F401
from tests.documents.conftest import generate, seal_cert  # noqa: F401
from tests.fulldoc.conftest import (  # noqa: F401
    create_sub,
    force_approve,
    member,
    signed_project,
)
from tests.subdocuments.conftest import (  # noqa: F401
    analyst,
    approved_entry,
    make_subdocument,
    manager,
    project,
    standard,
)

MAPPING = """
produto:
  entidade: TESTE_PRODUTO
  campos: {codigo: CODPROD, descricao: DESCRPROD, unidade: CODVOL, situacao: ATIVO}
registros:
  projeto:
    entidade: TESTE_PROJETO
    chave: CHAVE
    campos: {codigo_projeto: CODPROJ, nome: NOME, versao_projeto: VERSAO}
  documento:
    entidade: TESTE_DOCUMENTO
    chave: CHAVE
    campos: {codigo_projeto: CODPROJ, tipo_subdocumento: TIPO, versao_documento: VERSAO, elaborador: ELABORADOR, aprovador: APROVADOR, resumo_conteudo: RESUMO,
              pdf_sha256: PDFHASH, pdf_codigo_verificacao: PDFCOD}
  lote:
    entidade: TESTE_LOTE
    chave: CHAVE
    campos: {codigo_lote: CODLOTE}
  insumo_novo:
    entidade: TESTE_INSUMO
    chave: CHAVE
    campos: {descricao: DESCRICAO, situacao: SITUACAO, certificado_sha256: CERTIFICADO}
  resultado_estudo:
    entidade: TESTE_ESTUDO
    chave: CHAVE
    campos: {titulo: TITULO, conclusao: CONCLUSAO}
"""


class FakeGateway:
    def __init__(self):
        self.x_token = "x-token-ficticio"
        self.tokens = 0
        self.valid = set()
        self.calls = []
        self.records: dict[str, dict] = {}
        self.products: dict[str, dict] = {}
        self.fail = 0
        self.unauthorized = 0
        self.forms = []


def _handler(state: FakeGateway):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            return

        def _send(self, status, payload):
            data = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):  # noqa: N802 - nome exigido pelo http.server
            body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
            url = urlparse(self.path)
            if url.path == "/authenticate":
                form = parse_qs(body.decode())
                state.forms.append(form)
                ok = (
                    self.headers.get("X-Token") == state.x_token
                    and form.get("grant_type") == ["client_credentials"]
                    and form.get("client_id") == ["cliente-ficticio"]
                    and form.get("client_secret") == ["segredo-ficticio"]
                )
                if not ok:
                    return self._send(401, {"error": "invalid_client"})
                state.tokens += 1
                token = f"token-{state.tokens}"
                state.valid.add(token)
                return self._send(200, {"access_token": token, "expires_in": 3600})
            if url.path != "/gateway/v1/mge/service.sbr":
                return self._send(404, {})
            if state.unauthorized:
                state.unauthorized -= 1
                state.valid.clear()
                return self._send(401, {})
            if self.headers.get("Authorization", "").removeprefix("Bearer ") not in state.valid:
                return self._send(401, {})
            if state.fail:
                state.fail -= 1
                return self._send(500, {"status": "0"})
            service = parse_qs(url.query)["serviceName"][0]
            payload = json.loads(body)
            state.calls.append(service)
            data_set = payload["requestBody"]["dataSet"]
            if service == "CRUDServiceProvider.saveRecord":
                local = data_set["dataRow"]["localFields"]
                key_field = next(iter(local))
                fields = {name: value["$"] for name, value in local.items()}
                state.records.setdefault(data_set["rootEntity"], {})[fields[key_field]] = fields
                return self._send(200, {"status": "1", "responseBody": {}})
            if service == "CRUDServiceProvider.loadRecords":
                code = data_set["criteria"]["parameter"][0]["$"]
                names = data_set["entity"]["fieldset"]["list"].split(",")
                entities = {
                    "total": "0",
                    "metadata": {"fields": {"field": [{"name": n} for n in names]}},
                }
                product = state.products.get(code)
                if product:
                    entities["total"] = "1"
                    entities["entity"] = {
                        f"f{i}": {"$": product.get(n, "")} for i, n in enumerate(names)
                    }
                return self._send(200, {"status": "1", "responseBody": {"entities": entities}})
            return self._send(200, {"status": "0", "statusMessage": "Serviço não permitido"})

    return Handler


@pytest.fixture
def gateway(settings):
    from django.core.cache import cache

    state = FakeGateway()
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler(state))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    settings.SANKHYA_ENABLED = True
    settings.SANKHYA_BASE_URL = f"http://127.0.0.1:{server.server_address[1]}"
    settings.SANKHYA_CLIENT_ID = "cliente-ficticio"
    settings.SANKHYA_CLIENT_SECRET = "segredo-ficticio"
    settings.SANKHYA_X_TOKEN = state.x_token
    settings.SANKHYA_TIMEOUT = 5
    cache.delete("integrations:sankhya:token")
    yield state
    server.shutdown()
    server.server_close()
    cache.delete("integrations:sankhya:token")


@pytest.fixture
def it_admin(make_user):
    from sgp.accounts.profiles import Profile

    return make_user(None, Profile.ADMIN)


@pytest.fixture
def configured(it_admin):
    from sgp.integrations import services

    return services.publish_mapping(by=it_admin, text=MAPPING, note="Mapeamento de teste")
