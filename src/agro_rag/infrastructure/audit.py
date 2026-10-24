"""Structured operational audit adapter with a closed, non-sensitive schema."""

import json
import logging
from dataclasses import asdict

from agro_rag.application.audit import QueryAuditEvent


class LoggingAuditSink:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger("agro_rag.audit")

    def record(self, event: QueryAuditEvent) -> None:
        payload = {"event": "query_completed", **asdict(event)}
        self.logger.info(json.dumps(payload, ensure_ascii=True, separators=(",", ":")))
