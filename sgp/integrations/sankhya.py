"""Cliente do API Gateway da Sankhya (research R1 da feature 012).

Só o gateway oficial: autenticação OAuth 2.0 client credentials e serviços `CRUDServiceProvider`.
Credenciais só das variáveis de ambiente; nenhuma mensagem de erro inclui credencial ou token.
"""

import json
from urllib import error, parse, request

from django.conf import settings
from django.core.cache import cache

TOKEN_KEY = "integrations:sankhya:token"


class SankhyaError(Exception):
    """O gateway recusou a chamada ou respondeu fora do esperado."""


class SankhyaUnavailable(SankhyaError):
    """Gateway fora do ar, tempo esgotado ou integração não configurada."""


def configured() -> bool:
    return bool(
        settings.SANKHYA_ENABLED
        and settings.SANKHYA_BASE_URL
        and settings.SANKHYA_CLIENT_ID
        and settings.SANKHYA_CLIENT_SECRET
        and settings.SANKHYA_X_TOKEN
    )


def _base() -> str:
    return settings.SANKHYA_BASE_URL.rstrip("/")


def _post(url: str, data: bytes, headers: dict) -> tuple[int, dict]:
    req = request.Request(url, data=data, headers=headers, method="POST")  # noqa: S310 - só o gateway configurado
    try:
        with request.urlopen(req, timeout=settings.SANKHYA_TIMEOUT) as response:  # noqa: S310
            status, body = response.status, response.read()
    except error.HTTPError as exc:
        status, body = exc.code, exc.read() or b""
    except (error.URLError, TimeoutError, OSError) as exc:
        raise SankhyaUnavailable(
            f"Gateway da Sankhya indisponível ({exc.__class__.__name__})."
        ) from exc
    try:
        payload = json.loads(body.decode("utf-8") or "{}")
    except ValueError:
        payload = {}
    return status, payload


def token(*, force: bool = False) -> str:
    if not configured():
        raise SankhyaUnavailable("Integração com o Sankhya desligada ou sem credenciais.")
    if not force:
        cached = cache.get(TOKEN_KEY)
        if cached:
            return cached
    body = parse.urlencode(
        {
            "client_id": settings.SANKHYA_CLIENT_ID,
            "client_secret": settings.SANKHYA_CLIENT_SECRET,
            "grant_type": "client_credentials",
        }
    ).encode()
    status, data = _post(
        f"{_base()}/authenticate",
        body,
        {"Content-Type": "application/x-www-form-urlencoded", "X-Token": settings.SANKHYA_X_TOKEN},
    )
    if status >= 500:
        raise SankhyaUnavailable(f"Autenticação no gateway respondeu {status}.")
    access = data.get("access_token")
    if status != 200 or not access:
        raise SankhyaError(f"Autenticação no gateway recusada ({status}).")
    ttl = max(int(data.get("expires_in") or 300) - 60, 30)
    cache.set(TOKEN_KEY, access, ttl)
    return access


def call(body: dict) -> dict:
    """Chama o serviço do corpo; renova o token uma vez se o gateway responder 401."""
    service = body["serviceName"]
    url = f"{_base()}/gateway/v1/mge/service.sbr?" + parse.urlencode(
        {"serviceName": service, "outputType": "json"}
    )
    data = json.dumps(body).encode("utf-8")
    for attempt in (1, 2):
        access = token(force=attempt == 2)
        status, payload = _post(
            url, data, {"Content-Type": "application/json", "Authorization": f"Bearer {access}"}
        )
        if status == 401 and attempt == 1:
            cache.delete(TOKEN_KEY)
            continue
        if status >= 500:
            raise SankhyaUnavailable(f"Gateway respondeu {status} em {service}.")
        if status != 200:
            raise SankhyaError(f"Gateway respondeu {status} em {service}.")
        if str(payload.get("status")) != "1":
            message = str(payload.get("statusMessage") or "chamada recusada")[:300]
            raise SankhyaError(f"{service}: {message}")
        return payload
    raise SankhyaError(f"Token recusado pelo gateway em {service}.")
