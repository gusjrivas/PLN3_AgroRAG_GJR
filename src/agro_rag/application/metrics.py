"""Request-scoped port for fixed query and retrieval outcomes."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Protocol

from agro_rag.application.audit import AuditOutcome


class QueryMetrics(Protocol):
    def outcome(self, outcome: AuditOutcome) -> None: ...

    def cache_lookup(self, hit: bool) -> None: ...


query_metrics: ContextVar[QueryMetrics | None] = ContextVar("query_metrics", default=None)


@contextmanager
def bind_query_metrics(metrics: QueryMetrics | None) -> Iterator[None]:
    token = query_metrics.set(metrics)
    try:
        yield
    finally:
        query_metrics.reset(token)
