import httpx
import pytest


def test_http_client_uses_key_and_query_contract():
    from agro_rag_ui.client import ApiClient

    seen = []

    def handle(request):
        seen.append(request)
        return httpx.Response(200, json={"status": "needs_clarification"})

    with httpx.Client(transport=httpx.MockTransport(handle)) as http:
        client = ApiClient("http://localhost:8000", "test-secret", http)
        assert client.query("riego", "lettuce", {})["status"] == "needs_clarification"
    assert seen[0].headers["X-API-Key"] == "test-secret"
    assert seen[0].url.path == "/v1/query"


def test_backend_error_does_not_leak_body():
    from agro_rag_ui.client import ApiClient, ApiError

    with httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(502, text="SECRET provider info"))
    ) as http:
        with pytest.raises(ApiError) as exc:
            ApiClient("http://localhost:8000", "key", http).search("riego", None)
    assert "SECRET" not in str(exc.value)


@pytest.mark.parametrize(
    ("status", "code", "expected"),
    [
        (503, "NOT_READY", "modelo no está configurado"),
        (504, "DEADLINE", "tardó demasiado"),
        (502, "MODEL_INVALID", "no produjo una respuesta válida"),
    ],
)
def test_backend_typed_errors_have_safe_actionable_messages(status, code, expected):
    from agro_rag_ui.client import ApiClient, ApiError

    body = {
        "error": {
            "code": code,
            "message": "SECRET provider detail",
            "request_id": "request-id",
            "retryable": True,
        }
    }
    with httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(status, json=body))
    ) as http:
        with pytest.raises(ApiError) as exc:
            ApiClient("http://localhost:8000", "key", http).query("riego", None, {})

    assert expected in str(exc.value)
    assert "SECRET" not in str(exc.value)
