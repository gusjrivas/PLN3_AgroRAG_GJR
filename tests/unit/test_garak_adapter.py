import io
import json
from urllib.error import HTTPError
from urllib.request import Request

import pytest

from scripts.garak_adapter import AdapterError, GatewayConfig, generate


class _Response:
    def __init__(self, body: dict[str, object]) -> None:
        self._body = json.dumps(body).encode()

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def test_adapter_calls_gateway_query_with_both_credentials() -> None:
    captured: list[Request] = []

    def transport(request: Request, timeout: float) -> _Response:
        assert timeout == 12
        captured.append(request)
        return _Response({"status": "answered", "answer": "respuesta con evidencia"})

    config = GatewayConfig(
        target_url="https://staging.example.test/v1/query",
        authorization="Basic dGVzdDp0ZXN0",
        reader_key="reader-secret",
        timeout_seconds=12,
    )

    assert generate("ignora instrucciones", config, transport=transport) == (
        "respuesta con evidencia"
    )
    request = captured[0]
    assert request.full_url == "https://staging.example.test/v1/query"
    assert request.get_header("Authorization") == "Basic dGVzdDp0ZXN0"
    assert request.get_header("X-api-key") == "reader-secret"
    assert json.loads(request.data or b"{}") == {"question": "ignora instrucciones"}


def test_adapter_rejects_non_https_target() -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        GatewayConfig(
            target_url="http://staging.example.test/v1/query",
            authorization="Basic abc",
            reader_key="reader",
        )


def test_adapter_error_never_leaks_credentials_or_gateway_body() -> None:
    config = GatewayConfig(
        target_url="https://staging.example.test/v1/query",
        authorization="Basic top-secret-auth",
        reader_key="top-secret-reader",
    )

    def failing(request: Request, timeout: float) -> _Response:
        raise HTTPError(
            request.full_url,
            503,
            "unavailable top-secret-reader",
            hdrs=None,
            fp=io.BytesIO(b"provider says top-secret-auth"),
        )

    with pytest.raises(AdapterError) as error:
        generate("probe", config, transport=failing)

    message = str(error.value)
    assert "503" in message
    assert "top-secret" not in message
