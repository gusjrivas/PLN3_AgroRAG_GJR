from threading import Event

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
        self.fail_role = None

    async def generate(self, role, payload, timeout):
        if self.fail or self.fail_role == role:
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
        return Generation({"decision": "approve", "feedback": ""}, 80, 10, estimated=True)


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


def test_manual_tracing_ignores_fastapi_auto_configuration(
    exporters, monkeypatch, caplog, tmp_path
):
    monkeypatch.setenv("FASTAPI_OTEL_AUTO_CONFIGURE", "true")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "invalid-endpoint-sentinel")
    settings = Settings(
        _env_file=None, reader_key=KEY, tracing_enabled=True, catalogue_path=tmp_path
    )
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


@pytest.mark.parametrize("collector_status", [200, 400, None])
def test_otlp_exports_private_traces_and_aggregates(monkeypatch, collector_status):
    pytest.importorskip("opentelemetry.exporter.otlp.proto.http")
    from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import (
        ExportMetricsServiceRequest,
    )
    from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
    from requests import Response, Session
    from requests.exceptions import ConnectionError

    packets = []
    request_attempted = Event()

    def send(self, request, **kwargs):
        packets.append(request)
        request_attempted.set()
        if collector_status is None:
            raise ConnectionError("collector unavailable")
        response = Response()
        response.status_code = collector_status
        response._content = b""
        return response

    monkeypatch.setattr(Session, "send", send)
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_HEADERS", "x-secret=header-sentinel")
    monkeypatch.setenv("AGRO_TRACING_ENABLED", "true")
    monkeypatch.setenv("AGRO_OTLP_ENDPOINT", "http://collector:4318")
    settings = Settings(_env_file=None, reader_key=KEY)
    model = Model()
    service = QueryService(Retriever(), model, "v1")
    with TestClient(create_app(settings, service=service)) as client:
        assert post(client).status_code == 200
        if collector_status != 200:
            assert request_attempted.wait(timeout=5)
        assert post(client).status_code == 200
        assert post(client, "").status_code == 422
        model.fail_role = "verifier"
        assert post(client).status_code == 502

    traces = []
    metrics = []
    for packet in packets:
        assert b"sentinel" not in packet.body
        assert "x-secret" not in packet.headers
        if packet.url == "http://collector:4318/v1/traces":
            traces.extend(ExportTraceServiceRequest.FromString(packet.body).resource_spans)
        elif packet.url == "http://collector:4318/v1/metrics":
            metrics.extend(ExportMetricsServiceRequest.FromString(packet.body).resource_metrics)
        else:
            pytest.fail("Unexpected OTLP endpoint")

    unique_spans = {
        span.span_id: span
        for resource in traces
        for scope in resource.scope_spans
        for span in scope.spans
    }
    spans = list(unique_spans.values())
    roots = [span for span in spans if span.name == "POST /v1/query"]
    child_counts = [sum(span.parent_span_id == root.span_id for span in spans) for root in roots]
    assert sorted(child_counts) == [0, 3, 3, 3]
    for root in roots:
        assert all(
            span.trace_id == root.trace_id for span in spans if span.parent_span_id == root.span_id
        )
    points = {
        metric.name: getattr(metric, metric.WhichOneof("data")).data_points
        for resource in metrics
        for scope in resource.scope_metrics
        for metric in scope.metrics
    }
    assert {
        p.attributes[0].value.string_value: p.as_int for p in points["agro_rag.query.requests"]
    } == {"200": 2, "422": 1, "502": 1}
    assert sum(p.count for p in points["agro_rag.query.duration"]) == 4
    assert {
        p.attributes[0].value.string_value: p.as_int for p in points["agro_rag.query.outcomes"]
    } == {"answered": 2, "operational_error": 1}
    assert {
        p.attributes[0].value.string_value: p.as_int
        for p in points["agro_rag.retrieval.cache.lookups"]
    } == {"hit": 2, "miss": 1}
    assert {
        tuple(sorted((a.key, a.value.string_value) for a in p.attributes)): p.as_int
        for p in points["agro_rag.llm.tokens"]
    } == {
        (("direction", "input"), ("role", "researcher"), ("source", "reported")): 300,
        (("direction", "output"), ("role", "researcher"), ("source", "reported")): 60,
        (("direction", "input"), ("role", "verifier"), ("source", "estimated")): 160,
        (("direction", "output"), ("role", "verifier"), ("source", "estimated")): 20,
    }
    assert not any(p.exemplars for data_points in points.values() for p in data_points)


@pytest.mark.parametrize(
    "endpoint", ["http://user:pass@collector:4318", "http://collector:4318/v1/traces?x=1"]
)
def test_otlp_origin_rejects_embedded_credentials_and_paths(endpoint):
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="AGRO_OTLP_ENDPOINT"):
        Settings(_env_file=None, tracing_enabled=True, otlp_endpoint=endpoint)
