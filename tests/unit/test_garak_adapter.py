import io
import json
from urllib.error import HTTPError
from urllib.request import Request

import pytest

from scripts.garak_adapter import AdapterError, AdapterStats, GatewayConfig, generate


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
        return _Response(
            {
                "status": "answered",
                "answer": "respuesta con evidencia",
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }
        )

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


def test_adapter_treats_422_as_an_observable_contract_rejection() -> None:
    config = GatewayConfig(
        target_url="https://staging.example.test/v1/query",
        authorization="Basic dGVzdDp0ZXN0",
        reader_key="reader-secret",
    )
    outcomes: list[str] = []

    def rejected(request: Request, timeout: float) -> _Response:
        raise HTTPError(
            request.full_url,
            422,
            "validation failed",
            hdrs=None,
            fp=io.BytesIO(b'{"detail":"SECRET-PROMPT"}'),
        )

    result = generate(
        "probe fuera del contrato",
        config,
        transport=rejected,
        on_result=outcomes.append,
    )

    assert result == "La entrada fue rechazada por el contrato público de la API."
    assert outcomes == ["contract_rejected"]
    assert "SECRET-PROMPT" not in result


def test_adapter_still_fails_closed_for_non_validation_errors() -> None:
    config = GatewayConfig(
        target_url="https://staging.example.test/v1/query",
        authorization="Basic dGVzdDp0ZXN0",
        reader_key="reader-secret",
    )
    outcomes: list[str] = []

    def unavailable(request: Request, timeout: float) -> _Response:
        raise HTTPError(request.full_url, 503, "unavailable", hdrs=None, fp=None)

    with pytest.raises(AdapterError, match="503"):
        generate("probe", config, transport=unavailable, on_result=outcomes.append)

    assert outcomes == ["error"]


def test_adapter_reserves_worst_case_cost_before_calling_gateway() -> None:
    config = GatewayConfig(
        target_url="https://staging.example.test/v1/query",
        authorization="Basic dGVzdDp0ZXN0",
        reader_key="reader-secret",
        max_cost_usd="0.11",
    )
    stats = AdapterStats(config.max_cost_nano_usd)
    calls = 0

    def transport(request: Request, timeout: float) -> _Response:
        nonlocal calls
        calls += 1
        return _Response(
            {
                "status": "answered",
                "answer": "no debe ejecutarse",
                "usage": {"input_tokens": 1, "output_tokens": 1},
            }
        )

    result = generate("probe", config, transport=transport, stats=stats)

    assert result == "El presupuesto máximo de la prueba fue alcanzado."
    assert calls == 0
    assert stats.snapshot()["budget_exhausted"] == 1
    assert stats.snapshot()["spent_nano_usd"] == 0


def test_adapter_reconciles_reservation_with_reported_usage() -> None:
    config = GatewayConfig(
        target_url="https://staging.example.test/v1/query",
        authorization="Basic dGVzdDp0ZXN0",
        reader_key="reader-secret",
        max_cost_usd="0.20",
    )
    stats = AdapterStats(config.max_cost_nano_usd)

    def transport(request: Request, timeout: float) -> _Response:
        return _Response(
            {
                "status": "answered",
                "answer": "respuesta",
                "usage": {"input_tokens": 1_000, "output_tokens": 100},
            }
        )

    assert generate("probe", config, transport=transport, stats=stats) == "respuesta"
    metrics = stats.snapshot()
    assert metrics["input_tokens"] == 1_000
    assert metrics["output_tokens"] == 100
    assert metrics["spent_nano_usd"] == 3_500_000
    assert metrics["reserved_nano_usd"] == 0
    assert metrics["max_cost_nano_usd"] == 200_000_000


def test_concurrent_reservations_cannot_cross_cost_cap() -> None:
    stats = AdapterStats(200_000_000)

    assert stats.reserve() is True
    assert stats.reserve() is False
    metrics = stats.snapshot()
    assert metrics["reserved_nano_usd"] == 120_000_000
    assert metrics["budget_exhausted"] == 1


def test_adapter_refunds_contract_rejection_and_charges_errors_conservatively() -> None:
    config = GatewayConfig(
        target_url="https://staging.example.test/v1/query",
        authorization="Basic dGVzdDp0ZXN0",
        reader_key="reader-secret",
        max_cost_usd="0.20",
    )
    rejected_stats = AdapterStats(config.max_cost_nano_usd)
    failed_stats = AdapterStats(config.max_cost_nano_usd)

    def rejected(request: Request, timeout: float) -> _Response:
        raise HTTPError(request.full_url, 422, "invalid", hdrs=None, fp=None)

    def failed(request: Request, timeout: float) -> _Response:
        raise HTTPError(request.full_url, 503, "failed", hdrs=None, fp=None)

    generate("probe", config, transport=rejected, stats=rejected_stats)
    with pytest.raises(AdapterError):
        generate("probe", config, transport=failed, stats=failed_stats)

    assert rejected_stats.snapshot()["spent_nano_usd"] == 0
    assert failed_stats.snapshot()["spent_nano_usd"] == 120_000_000


@pytest.mark.parametrize("value", ["0", "-1", "0.200000001", "invalid"])
def test_gateway_config_rejects_invalid_or_over_cap_budget(value: str) -> None:
    with pytest.raises(ValueError, match="presupuesto"):
        GatewayConfig(
            target_url="https://staging.example.test/v1/query",
            authorization="Basic dGVzdDp0ZXN0",
            reader_key="reader-secret",
            max_cost_usd=value,
        )
