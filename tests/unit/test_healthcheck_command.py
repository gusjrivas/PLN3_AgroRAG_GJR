import httpx

from agro_rag.bootstrap.settings import Settings


def test_healthcheck_uses_internal_url_and_reader_secret_without_proxy() -> None:
    from agro_rag.bootstrap.healthcheck import check_readiness

    seen: list[httpx.Request] = []

    def ready(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"status": "ready"})

    settings = Settings(
        reader_key="health-secret-sentinel-123456",
        healthcheck_url="http://api:8000/health/ready",
    )

    assert check_readiness(settings, transport=httpx.MockTransport(ready))
    assert seen[0].url == httpx.URL("http://api:8000/health/ready")
    assert seen[0].headers["X-API-Key"] == "health-secret-sentinel-123456"


def test_healthcheck_fails_closed_and_does_not_print_secret(capsys) -> None:
    from agro_rag.bootstrap.healthcheck import check_readiness

    secret = "health-error-secret-sentinel-123456"

    def unavailable(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(f"provider included {secret}", request=request)

    settings = Settings(reader_key=secret)

    assert not check_readiness(settings, transport=httpx.MockTransport(unavailable))
    captured = capsys.readouterr()
    assert secret not in captured.out
    assert secret not in captured.err


def test_healthcheck_fails_closed_without_reader_key() -> None:
    from agro_rag.bootstrap.healthcheck import check_readiness

    assert not check_readiness(Settings(reader_key=""))


def test_liveness_probe_does_not_require_or_send_reader_key() -> None:
    from agro_rag.bootstrap.healthcheck import check_readiness

    seen: list[httpx.Request] = []

    def live(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"status": "ok"})

    settings = Settings(
        reader_key="",
        healthcheck_url="http://127.0.0.1:8000/health/live",
        healthcheck_expected_status="ok",
    )

    assert check_readiness(settings, transport=httpx.MockTransport(live))
    assert "X-API-Key" not in seen[0].headers
