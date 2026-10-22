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
