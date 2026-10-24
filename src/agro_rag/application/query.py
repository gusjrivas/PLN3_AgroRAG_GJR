"""Bounded researcher/verifier interaction, independent of HTTP and LLM SDKs."""

import asyncio
import json
import time
import unicodedata
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import uuid4

from agro_rag.application.audit import AuditOutcome, AuditSink, QueryAuditEvent
from agro_rag.application.retrieval import Retriever
from agro_rag.domain.evidence import Evidence


class UpstreamError(Exception):
    pass


class BudgetExceeded(Exception):
    pass


@dataclass(frozen=True)
class Generation:
    data: dict[str, Any]
    input_tokens: int
    output_tokens: int
    estimated: bool = False


class Model(Protocol):
    async def generate(self, role: str, payload: dict[str, Any], timeout: float) -> Generation: ...


def normalize_question(question: str) -> str:
    plain = "".join(
        character
        for character in unicodedata.normalize("NFKD", question.casefold())
        if not unicodedata.combining(character)
    )
    return " ".join(plain.split())


class QueryService:
    def __init__(
        self,
        retriever: Retriever,
        model: Model,
        version: str,
        deadline_seconds: float = 60.0,
        retrieval_cache_size: int = 128,
        audit_sink: AuditSink | None = None,
    ) -> None:
        if retrieval_cache_size <= 0:
            raise ValueError("El tamaño de caché debe ser positivo")
        self.retriever = retriever
        self.model = model
        self.version = version
        self.deadline_seconds = deadline_seconds
        self.retrieval_cache_size = retrieval_cache_size
        self.audit_sink = audit_sink
        self._retrieval_cache: OrderedDict[tuple[str, str, str | None], tuple[Evidence, ...]] = (
            OrderedDict()
        )

    async def run(self, question: str, crop: str | None, context: dict[str, Any]) -> dict[str, Any]:
        request_id = str(uuid4())
        started = time.monotonic()
        try:
            async with asyncio.timeout(self.deadline_seconds):
                return await self._run(question, crop, context, request_id, started)
        except Exception as exc:
            exc.request_id = request_id  # type: ignore[attr-defined]
            self._record_audit(
                QueryAuditEvent(
                    request_id=request_id,
                    corpus_version=self.version,
                    outcome="operational_error",
                    decision="error",
                    revision_count=0,
                    total_ms=int((time.monotonic() - started) * 1000),
                    llm_calls=0,
                    input_tokens=0,
                    output_tokens=0,
                    estimated=False,
                    cache_hit=False,
                    error_type=self._safe_error_type(exc),
                )
            )
            raise

    def _record_audit(self, event: QueryAuditEvent) -> None:
        if self.audit_sink is not None:
            self.audit_sink.record(event)

    @staticmethod
    def _safe_error_type(exc: Exception) -> str:
        allowed = {
            "BudgetExceeded",
            "RetrievalContractError",
            "RetrievalUnavailable",
            "TimeoutError",
            "UpstreamError",
        }
        name = type(exc).__name__
        return name if name in allowed else "InternalError"

    async def _run(
        self,
        question: str,
        crop: str | None,
        context: dict[str, Any],
        request_id: str,
        started: float,
    ) -> dict[str, Any]:
        normalized = normalize_question(question)
        cache_key = (self.version, normalized, crop)
        try:
            hits = self._retrieval_cache.pop(cache_key)
            self._retrieval_cache[cache_key] = hits
            cache_hit = True
        except KeyError:
            hits = await asyncio.to_thread(self.retriever.search, question, crop)
            self._retrieval_cache[cache_key] = hits
            if len(self._retrieval_cache) > self.retrieval_cache_size:
                self._retrieval_cache.popitem(last=False)
            cache_hit = False
        available = {item.evidence_id: item for item in hits}
        usage = {
            "llm_calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated": False,
            "total_ms": 0,
            "cache_hit": cache_hit,
        }
        revision = 0
        decision = "abstain"

        def finish(
            status: AuditOutcome,
            claims: list[dict[str, Any]] | None = None,
            missing: list[str] | None = None,
        ) -> dict[str, Any]:
            claims = claims or []
            ids = dict.fromkeys(eid for claim in claims for eid in claim["evidence_ids"])
            citations = []
            for eid in ids:
                e = available[eid]
                citations.append(
                    {
                        "evidence_id": eid,
                        "source_id": e.source_id,
                        "title": e.title,
                        "edition": e.edition,
                        "pdf_page": e.pdf_page,
                        "printed_page": e.printed_page,
                        "section": e.section,
                        "excerpt": e.text,
                        "source_url": e.source_url,
                    }
                )
            usage["total_ms"] = int((time.monotonic() - started) * 1000)
            result = {
                "request_id": request_id,
                "status": status,
                "answer": "\n\n".join(c["text"] for c in claims)
                if claims
                else (
                    "Necesito más información para responder."
                    if missing
                    else "No hay evidencia suficiente para una respuesta verificada."
                ),
                "claims": claims,
                "citations": citations,
                "missing_information": missing or [],
                "limitations": [
                    "Corpus piloto; recuperación lexical, sin índice semántico todavía.",
                    "Verificación automática pendiente de evaluación agronómica.",
                ],
                "corpus_version": self.version,
                "verification": {
                    "decision": decision,
                    "revision_count": revision,
                    "issue_codes": [] if status == "answered" else ["NOT_VERIFIED"],
                },
                "usage": usage,
            }
            self._record_audit(
                QueryAuditEvent(
                    request_id=request_id,
                    corpus_version=self.version,
                    outcome=status,
                    decision=decision,
                    revision_count=revision,
                    total_ms=int(usage["total_ms"]),
                    llm_calls=int(usage["llm_calls"]),
                    input_tokens=int(usage["input_tokens"]),
                    output_tokens=int(usage["output_tokens"]),
                    estimated=bool(usage["estimated"]),
                    cache_hit=bool(usage["cache_hit"]),
                )
            )
            return result

        async def generate(role: str, payload: dict[str, Any]) -> dict[str, Any]:
            # Byte count is a conservative upper estimate for UTF-8 BPE input;
            # reserve room for the system instructions and capped output.
            reserve = len(json.dumps(payload, ensure_ascii=False).encode()) + 2048
            used = int(usage["input_tokens"]) + int(usage["output_tokens"])
            if usage["llm_calls"] >= 6 or used + reserve > 12000:
                raise BudgetExceeded("Presupuesto de tokens agotado")
            remaining = self.deadline_seconds - (time.monotonic() - started)
            if remaining <= 0:
                raise TimeoutError
            generated = await self.model.generate(role, payload, remaining)
            if generated.input_tokens < 0 or generated.output_tokens < 0:
                raise UpstreamError("Usage inválido")
            usage["llm_calls"] += 1
            usage["input_tokens"] += generated.input_tokens
            usage["output_tokens"] += generated.output_tokens
            usage["estimated"] = bool(usage["estimated"] or generated.estimated)
            if int(usage["input_tokens"]) + int(usage["output_tokens"]) > 12000:
                raise BudgetExceeded("Proveedor superó presupuesto")
            return generated.data

        if (
            ("litro" in normalized or "cuanto" in normalized)
            and ("riego" in normalized or "regar" in normalized)
            and not all(context.get(key) for key in ("growth_stage", "soil_description"))
        ):
            decision = "clarify"
            return finish(
                "needs_clarification",
                missing=[
                    "Indicar etapa del cultivo, tipo de suelo, superficie y condiciones de riego. "
                    "Un porcentaje de humedad no permite calcular litros por sí solo."
                ],
            )
        if not hits:
            return finish("insufficient_evidence")
        evidence = [
            {"evidence_id": e.evidence_id, "text": e.text, "source_id": e.source_id} for e in hits
        ]
        feedback = ""
        for pass_number in range(2):
            revision = pass_number
            draft = await generate(
                "researcher",
                {
                    "question": question,
                    "crop": crop,
                    "context": context,
                    "evidence": evidence,
                    "feedback": feedback,
                },
            )
            status = draft.get("status")
            if status == "needs_clarification":
                missing = draft.get("missing_information")
                if (
                    isinstance(missing, list)
                    and missing
                    and not any(
                        not isinstance(x, str) or not x.strip() or len(x) > 500 for x in missing
                    )
                ):
                    decision = "clarify"
                    return finish(status, missing=missing)
                if missing == [] and isinstance(draft.get("claims"), list) and draft["claims"]:
                    status = "answered"
                else:
                    raise UpstreamError("Aclaración inválida")
            if status == "insufficient_evidence":
                return finish(status)
            raw_claims = draft.get("claims")
            if (
                status != "answered"
                or not isinstance(raw_claims, list)
                or not 1 <= len(raw_claims) <= 12
            ):
                raise UpstreamError("Borrador inválido")
            claims = []
            for i, claim in enumerate(raw_claims, 1):
                if not isinstance(claim, dict):
                    raise UpstreamError("Claim inválido")
                text, ids = claim.get("text"), claim.get("evidence_ids")
                if (
                    not isinstance(text, str)
                    or not text.strip()
                    or len(text) > 1500
                    or not isinstance(ids, list)
                    or not ids
                    or any(not isinstance(eid, str) or eid not in available for eid in ids)
                ):
                    raise UpstreamError("Claim sin evidencia válida")
                claims.append(
                    {"claim_id": str(i), "text": text, "evidence_ids": list(dict.fromkeys(ids))}
                )
            review = await generate(
                "verifier", {"question": question, "claims": claims, "evidence": evidence}
            )
            decision = review.get("decision", "")
            feedback = review.get("feedback", "")
            if not isinstance(feedback, str) or len(feedback) > 1000:
                raise UpstreamError("Feedback inválido")
            if decision == "approve":
                return finish("answered", claims)
            if decision == "clarify" and feedback.strip():
                return finish("needs_clarification", missing=[feedback])
            if decision == "abstain":
                return finish("insufficient_evidence")
            if decision != "revise" or not feedback.strip():
                raise UpstreamError("Veredicto inválido")
        decision = "abstain"
        return finish("insufficient_evidence")
