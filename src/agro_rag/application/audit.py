"""Safe audit contracts; events intentionally exclude user and provider text."""

from dataclasses import dataclass
from typing import Literal, Protocol

AuditOutcome = Literal[
    "answered", "needs_clarification", "insufficient_evidence", "operational_error"
]


@dataclass(frozen=True)
class QueryAuditEvent:
    request_id: str
    corpus_version: str
    outcome: AuditOutcome
    decision: str
    revision_count: int
    total_ms: int
    llm_calls: int
    input_tokens: int
    output_tokens: int
    estimated: bool
    cache_hit: bool
    error_type: str | None = None


class AuditSink(Protocol):
    def record(self, event: QueryAuditEvent) -> None: ...
