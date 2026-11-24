"""OTLP/HTTP transport and the bounded set of dashboard instruments."""

from collections.abc import Callable

from opentelemetry.exporter.otlp.proto.http import Compression
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import AlwaysOffExemplarFilter, MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.metrics.view import ExplicitBucketHistogramAggregation, View
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from requests import PreparedRequest, Session

from agro_rag.application.audit import AuditOutcome
from agro_rag.application.metrics import LlmRole

_EXPORT_TIMEOUT_SECONDS = 2
_HEADERS = {"Content-Type": "application/x-protobuf"}
_DURATION = "agro_rag.query.duration"


def _collector_headers(request: PreparedRequest) -> PreparedRequest:
    # The exporter merges OTEL_* headers even when explicit headers are supplied.
    request.headers.clear()
    request.headers.update(_HEADERS)
    request.prepare_content_length(request.body)
    return request


def _exporter[Exporter: (OTLPSpanExporter, OTLPMetricExporter)](
    factory: Callable[..., Exporter], url: str
) -> Exporter:
    session = Session()
    session.trust_env = False
    session.auth = _collector_headers
    exporter = factory(
        endpoint=url,
        timeout=_EXPORT_TIMEOUT_SECONDS,
        headers=_HEADERS,
        compression=Compression.NoCompression,
        session=session,
    )
    session.cert = None
    session.verify = True
    return exporter


def otlp_span_processor(endpoint: str) -> BatchSpanProcessor:
    return BatchSpanProcessor(
        _exporter(OTLPSpanExporter, f"{endpoint}/v1/traces"),
        max_queue_size=512,
        max_export_batch_size=128,
        schedule_delay_millis=1000,
    )


class OtlpQueryMetrics:
    def __init__(self, endpoint: str, resource: Resource) -> None:
        reader = PeriodicExportingMetricReader(
            _exporter(OTLPMetricExporter, f"{endpoint}/v1/metrics"),
            export_interval_millis=5000,
            export_timeout_millis=2000,
        )
        self._provider = MeterProvider(
            resource=resource,
            metric_readers=[reader],
            shutdown_on_exit=False,
            exemplar_filter=AlwaysOffExemplarFilter(),
            views=[
                View(
                    instrument_name=_DURATION,
                    aggregation=ExplicitBucketHistogramAggregation(
                        boundaries=[0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 30, 45, 60, 90]
                    ),
                )
            ],
        )
        meter = self._provider.get_meter("agro-rag")
        self._requests = meter.create_counter("agro_rag.query.requests")
        self._duration = meter.create_histogram(_DURATION, unit="s")
        self._outcomes = meter.create_counter("agro_rag.query.outcomes")
        self._cache = meter.create_counter("agro_rag.retrieval.cache.lookups")
        self._tokens = meter.create_counter("agro_rag.llm.tokens")

    def http_completed(self, status: int, seconds: float) -> None:
        attributes = {"http.response.status_code": str(status)}
        self._requests.add(1, attributes)
        self._duration.record(seconds, attributes)

    def outcome(self, outcome: AuditOutcome) -> None:
        self._outcomes.add(1, {"outcome": outcome})

    def cache_lookup(self, hit: bool) -> None:
        self._cache.add(1, {"cache.result": "hit" if hit else "miss"})

    def llm_tokens(
        self, role: LlmRole, input_tokens: int, output_tokens: int, estimated: bool
    ) -> None:
        labels = {"role": role, "source": "estimated" if estimated else "reported"}
        self._tokens.add(input_tokens, {**labels, "direction": "input"})
        self._tokens.add(output_tokens, {**labels, "direction": "output"})

    def shutdown(self) -> None:
        self._provider.shutdown()
