"""Manual query tracing for the academic demo."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from os import getenv
from time import perf_counter

from opentelemetry.context import Context
from opentelemetry.sdk.environment_variables import OTEL_SDK_DISABLED
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.sdk.trace.sampling import ALWAYS_ON
from opentelemetry.trace import SpanKind, StatusCode

from agro_rag.application.metrics import bind_query_metrics
from agro_rag.application.tracing import Stage, bind_stage_tracer


class QueryTracing:
    def __init__(self, endpoint: str | None = None) -> None:
        if getenv(OTEL_SDK_DISABLED, "").strip().lower() == "true":
            raise RuntimeError("AGRO_TRACING_ENABLED conflicts with OTEL_SDK_DISABLED=true")
        # Construct directly to keep environment attributes and detectors out.
        resource = Resource({"service.name": "agro-rag"})
        self._metrics = None
        self._provider = TracerProvider(
            resource=resource,
            sampler=ALWAYS_ON,
            shutdown_on_exit=False,
        )
        if endpoint is None:
            self._provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        else:
            from agro_rag.infrastructure.otlp import OtlpQueryMetrics, otlp_span_processor

            origin = endpoint.rstrip("/")
            self._metrics = OtlpQueryMetrics(origin, resource)
            self._provider.add_span_processor(otlp_span_processor(origin))
        self._tracer = self._provider.get_tracer("agro-rag")

    @contextmanager
    def query(self) -> Iterator[Callable[[int], None]]:
        started = perf_counter()
        with (
            self._tracer.start_as_current_span(
                "POST /v1/query",
                context=Context(),
                kind=SpanKind.SERVER,
                record_exception=False,
                set_status_on_exception=False,
            ) as span,
            bind_stage_tracer(self._stage),
            bind_query_metrics(self._metrics),
        ):

            def record_status(code: int) -> None:
                span.set_attribute("http.response.status_code", code)
                if code >= 500:
                    span.set_status(StatusCode.ERROR)
                if self._metrics is not None:
                    self._metrics.http_completed(code, perf_counter() - started)

            yield record_status

    @contextmanager
    def _stage(self, stage: Stage) -> Iterator[None]:
        with self._tracer.start_as_current_span(
            stage, record_exception=False, set_status_on_exception=False
        ) as span:
            try:
                yield
            except BaseException:
                span.set_status(StatusCode.ERROR)
                raise

    def shutdown(self) -> None:
        try:
            self._provider.shutdown()
        finally:
            if self._metrics is not None:
                self._metrics.shutdown()
