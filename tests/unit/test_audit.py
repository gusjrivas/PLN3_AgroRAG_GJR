import asyncio
import json
import logging

import pytest


class RecordingAudit:
    def __init__(self):
        self.events = []

    def record(self, event):
        self.events.append(event)


class EmptyRetriever:
    def search(self, question, crop):
        return ()


class ForbiddenModel:
    async def generate(self, *args):
        raise AssertionError("model must not be called")


def test_ops_01_audit_records_safe_business_metadata_only():
    from agro_rag.application.query import QueryService

    sink = RecordingAudit()
    secret_question = "riego PINECONE_API_KEY=sentinel-secret"
    result = asyncio.run(
        QueryService(EmptyRetriever(), ForbiddenModel(), "v1", audit_sink=sink).run(
            secret_question, "tomato", {}
        )
    )

    assert result["status"] == "insufficient_evidence"
    assert len(sink.events) == 1
    event = sink.events[0]
    assert event.outcome == "insufficient_evidence"
    assert event.corpus_version == "v1"
    assert event.cache_hit is False
    assert event.error_type is None
    assert "sentinel-secret" not in repr(event)
    assert secret_question not in repr(event)


def test_ops_01_audit_redacts_operational_exception_details():
    from agro_rag.application.query import QueryService
    from agro_rag.application.retrieval_pipeline import RetrievalUnavailable

    class FailedRetriever:
        def search(self, question, crop):
            raise RetrievalUnavailable("PINECONE_API_KEY=sentinel-secret")

    sink = RecordingAudit()
    with pytest.raises(RetrievalUnavailable) as captured:
        asyncio.run(
            QueryService(FailedRetriever(), ForbiddenModel(), "v1", audit_sink=sink).run(
                "pregunta privada", None, {}
            )
        )

    assert len(sink.events) == 1
    event = sink.events[0]
    assert event.outcome == "operational_error"
    assert event.error_type == "RetrievalUnavailable"
    assert captured.value.request_id == event.request_id
    assert "sentinel-secret" not in repr(event)
    assert "pregunta privada" not in repr(event)


def test_logging_audit_sink_emits_structured_json_without_sensitive_fields(caplog):
    from agro_rag.application.audit import QueryAuditEvent
    from agro_rag.infrastructure.audit import LoggingAuditSink

    event = QueryAuditEvent(
        request_id="request-1",
        corpus_version="v1",
        outcome="answered",
        decision="approve",
        revision_count=0,
        total_ms=12,
        llm_calls=2,
        input_tokens=10,
        output_tokens=5,
        estimated=False,
        cache_hit=True,
    )
    caplog.set_level(logging.INFO, logger="agro_rag.audit")

    LoggingAuditSink().record(event)

    payload = json.loads(caplog.records[-1].message)
    assert payload["event"] == "query_completed"
    assert payload["request_id"] == "request-1"
    assert set(payload) == {
        "event",
        "request_id",
        "corpus_version",
        "outcome",
        "decision",
        "revision_count",
        "total_ms",
        "llm_calls",
        "input_tokens",
        "output_tokens",
        "estimated",
        "cache_hit",
        "error_type",
    }
