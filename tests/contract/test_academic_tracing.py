import pytest
from fastapi.testclient import TestClient

from agro_rag.application.query import Generation, QueryService, UpstreamError
from agro_rag.bootstrap.app import create_app
from agro_rag.bootstrap.settings import Settings
from agro_rag.domain.evidence import Evidence

KEY = "reader-secret-sentinel"
QUESTION = "riego lechuga question-sentinel"


class Retriever:
    def search(self, question, filters):
        return (
            Evidence(
                "a",
                "v1",
                "S",
                "Manual",
                "2008",
                "https://example.org/doc.pdf",
                3,
                "1",
                "Riego",
                "lettuce",
                "passage-sentinel",
                "passage-sentinel",
                0,
                16,
            ),
        )


class Model:
    def __init__(self, fail=False):
        self.fail = fail

    async def generate(self, role, payload, timeout):
        if self.fail:
            raise UpstreamError("exception-sentinel")
        if role == "researcher":
            return Generation(
                {
                    "status": "answered",
                    "claims": [{"text": "answer-sentinel", "evidence_ids": ["a"]}],
                },
                100,
                20,
            )
        return Generation({"decision": "approve", "feedback": ""}, 100, 20)


def post(client, question=QUESTION):
    return client.post(
        "/v1/query?private=query-string-sentinel",
        headers={
            "X-API-Key": KEY,
            "traceparent": "00-11111111111111111111111111111111-1111111111111111-01",
        },
        json={"question": question, "crop": "lettuce"},
    )


def test_tracing_defaults_to_disabled(monkeypatch):
    monkeypatch.delenv("AGRO_TRACING_ENABLED", raising=False)
    settings = Settings(_env_file=None, reader_key=KEY)
    with TestClient(
        create_app(settings, service=QueryService(Retriever(), Model(), "v1"))
    ) as client:
        assert post(client).status_code == 200
    assert settings.model_dump().get("tracing_enabled") is False


@pytest.fixture
def exporters(monkeypatch):
    pytest.importorskip("opentelemetry.sdk")
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    from agro_rag.infrastructure import tracing

    instances = []

    class Exporter(InMemorySpanExporter):
        closed = False

        def __init__(self):
            super().__init__()
            instances.append(self)

        def shutdown(self):
            self.closed = True
            super().shutdown()

    monkeypatch.setattr(tracing, "ConsoleSpanExporter", Exporter)
    return instances


def test_enabled_factories_isolate_traces_and_close(exporters, monkeypatch):
    from opentelemetry import trace

    original_provider = trace.get_tracer_provider()
    monkeypatch.setenv("AGRO_TRACING_ENABLED", "true")
    monkeypatch.setenv("OTEL_RESOURCE_ATTRIBUTES", "private=resource-sentinel")
    settings = Settings(reader_key=KEY)
    service = QueryService(Retriever(), Model(), "v1")
    with (
        TestClient(create_app(settings, service=service)) as first,
        TestClient(
            create_app(settings, service=QueryService(Retriever(), Model(True), "v1"))
        ) as second,
        TestClient(
            create_app(Settings(reader_key=KEY, tracing_enabled=False), service=service)
        ) as off,
    ):
        assert post(first).status_code == 200
        assert post(second).status_code == 502
        assert post(first, "").status_code == 422
        assert post(off).status_code == 200
        assert first.get("/health/live").status_code == 200
        assert len(exporters) == 2
        success, failure = [exporter.get_finished_spans() for exporter in exporters]

    assert settings.tracing_enabled
    assert all(exporter.closed for exporter in exporters)
    assert trace.get_tracer_provider() is original_provider
    assert [span.name for span in success] == [
        "retrieval",
        "researcher",
        "verifier",
        "POST /v1/query",
        "POST /v1/query",
    ]
    assert [span.name for span in failure] == ["retrieval", "researcher", "POST /v1/query"]
    for spans, status in [(success[:4], 200), (failure, 502), (success[4:], 422)]:
        root = spans[-1]
        assert root.parent is None
        assert root.context.trace_id != int("1" * 32, 16)
        assert root.attributes == {"http.response.status_code": status}
        for child in spans[:-1]:
            assert child.parent == root.context
            assert child.attributes == {}
        for span in spans:
            assert span.resource.attributes == {"service.name": "agro-rag"}
            assert not span.events
            assert span.status.description is None
            assert "sentinel" not in span.to_json()
    assert failure[1].status.status_code is trace.StatusCode.ERROR


def test_manual_tracing_ignores_fastapi_auto_configuration(exporters, monkeypatch, caplog):
    monkeypatch.setenv("FASTAPI_OTEL_AUTO_CONFIGURE", "true")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "invalid-endpoint-sentinel")
    settings = Settings(reader_key=KEY, tracing_enabled=True)
    with TestClient(create_app(settings)) as client:
        assert post(client).status_code == 503
    assert "FastAPI automatic telemetry configuration failed" not in caplog.text
    assert len(exporters) == 1
    (span,) = exporters[0].get_finished_spans()
    assert span.attributes == {"http.response.status_code": 503}


def test_tracing_rejects_disabled_sdk(exporters, monkeypatch):
    monkeypatch.setenv("OTEL_SDK_DISABLED", "true")
    settings = Settings(reader_key=KEY, tracing_enabled=True)
    with pytest.raises(RuntimeError, match="OTEL_SDK_DISABLED"):
        with TestClient(create_app(settings)):
            pytest.fail("Tracing-enabled API started without a recording SDK")
