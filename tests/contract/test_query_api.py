import pytest
from fastapi.testclient import TestClient

from agro_rag.application.query import BudgetExceeded, UpstreamError

KEY = "test-reader-token-123456"


def client():
    from agro_rag.bootstrap.app import create_app
    from agro_rag.bootstrap.settings import Settings

    return TestClient(create_app(Settings(reader_key=KEY)))


def test_auth_and_unavailable_are_distinct():
    with client() as c:
        assert c.post("/v1/query", json={"question": "riego"}).status_code == 401
        r = c.post("/v1/query", headers={"X-API-Key": KEY}, json={"question": "riego"})
        assert r.status_code == 503 and r.json()["error"]["code"] == "NOT_READY"
        assert c.get("/health/live").status_code == 200


def test_input_validation():
    with client() as c:
        for question in ["", "   ", "a" * 2001]:
            assert (
                c.post(
                    "/v1/query", headers={"X-API-Key": KEY}, json={"question": question}
                ).status_code
                == 422
            )
        assert (
            c.post(
                "/v1/query",
                headers={"X-API-Key": KEY},
                json={"question": "riego", "context": {"measurement": {"value": 30}}},
            ).status_code
            == 422
        )
        assert (
            c.post(
                "/v1/query",
                headers={"X-API-Key": KEY},
                json={
                    "question": "riego",
                    "context": {
                        "measurement": {
                            "value": 101,
                            "unit": "%",
                            "measurement_type": "volumetric_water_content",
                        }
                    },
                },
            ).status_code
            == 422
        )


def test_catalogue_search_and_versioned_evidence():
    from agro_rag.bootstrap.app import create_app
    from agro_rag.bootstrap.settings import Settings
    from agro_rag.domain.evidence import Catalogue, Evidence

    e = Evidence(
        "abc",
        "v1",
        "S",
        "Manual",
        "2008",
        "https://example.org/doc.pdf",
        3,
        "1",
        "Riego",
        "lettuce",
        "Humedad constante",
        "Humedad constante",
        0,
        17,
    )
    with TestClient(create_app(Settings(reader_key=KEY), catalogue=Catalogue("v1", (e,)))) as c:
        h = {"X-API-Key": KEY}
        assert c.get("/v1/corpus", headers=h).json()["evidence_count"] == 1
        response = c.get("/v1/preview/search", params={"question": "humedad"}, headers=h)
        assert response.status_code == 200
        assert response.json()["mode"] == "lexical_preview"
        assert response.json()["evidence"][0]["evidence_id"] == "abc"
        assert c.get("/v1/evidence/abc?corpus_version=other", headers=h).status_code == 404
        result = c.get("/v1/evidence/abc?corpus_version=v1", headers=h).json()
        assert result["pdf_page"] == 3 and result["printed_page"] == "1"
        assert "original_text" not in result


def test_query_response_schema_and_end_to_end_fake_provider():
    from agro_rag.application.query import Generation, QueryService
    from agro_rag.bootstrap.app import create_app
    from agro_rag.bootstrap.settings import Settings
    from agro_rag.domain.evidence import Catalogue, Evidence
    from agro_rag.infrastructure.retrieval import LexicalRetriever

    e = Evidence(
        "abc",
        "v1",
        "S",
        "Manual",
        "2008",
        "https://example.org/doc.pdf",
        3,
        "1",
        "Riego",
        "lettuce",
        "Humedad constante",
        "Humedad constante",
        0,
        17,
    )
    cat = Catalogue("v1", (e,))

    class Model:
        async def generate(self, role, payload, timeout):
            if role == "researcher":
                return Generation(
                    {
                        "status": "answered",
                        "claims": [
                            {"text": "Mantener humedad constante.", "evidence_ids": ["abc"]}
                        ],
                    },
                    20,
                    10,
                )
            return Generation({"decision": "approve", "feedback": ""}, 20, 10)

    service = QueryService(LexicalRetriever(cat), Model(), "v1")
    with TestClient(create_app(Settings(reader_key=KEY), catalogue=cat, service=service)) as c:
        response = c.post(
            "/v1/query", headers={"X-API-Key": KEY}, json={"question": "humedad", "crop": "lettuce"}
        )
        assert response.status_code == 200 and response.json()["status"] == "answered"
        assert response.json()["citations"][0]["pdf_page"] == 3
        schema = c.get("/openapi.json").json()["paths"]["/v1/query"]["post"]["responses"]["200"][
            "content"
        ]["application/json"]["schema"]
        assert schema["$ref"].endswith("/QueryResponse")


@pytest.mark.parametrize(
    "failure,status",
    [(TimeoutError(), 504), (UpstreamError("SECRET"), 502), (BudgetExceeded(), 429)],
)
def test_provider_failures_are_typed_and_redacted(failure, status):
    from agro_rag.bootstrap.app import create_app
    from agro_rag.bootstrap.settings import Settings

    class FailedService:
        async def run(self, *args):
            raise failure

    with TestClient(create_app(Settings(reader_key=KEY), service=FailedService())) as c:
        response = c.post("/v1/query", headers={"X-API-Key": KEY}, json={"question": "riego"})
        assert response.status_code == status
        assert "SECRET" not in response.text
        assert response.json()["error"]["request_id"]
        assert c.get("/health/ready", headers={"X-API-Key": KEY}).status_code == 200


def test_only_two_queries_can_run_at_once():
    import asyncio

    import httpx

    from agro_rag.bootstrap.app import create_app
    from agro_rag.bootstrap.settings import Settings

    class BlockedService:
        def __init__(self):
            self.started = 0
            self.release = asyncio.Event()

        async def run(self, *args):
            self.started += 1
            await self.release.wait()
            raise TimeoutError

    async def exercise():
        service = BlockedService()
        app = create_app(Settings(reader_key=KEY), service=service)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as c:

            async def request():
                return await c.post(
                    "/v1/query", headers={"X-API-Key": KEY}, json={"question": "riego"}
                )

            first = asyncio.create_task(request())
            second = asyncio.create_task(request())
            for _ in range(100):
                if service.started == 2:
                    break
                await asyncio.sleep(0.001)
            try:
                assert (await request()).status_code == 429
            finally:
                service.release.set()
                await asyncio.gather(first, second)
            assert (await request()).status_code == 504

    asyncio.run(exercise())


def test_non_ascii_invalid_key_is_rejected_without_server_error():
    with client() as c:
        response = c.post("/v1/query", headers={b"X-API-Key": b"\xff"}, json={"question": "riego"})
        assert response.status_code == 401
