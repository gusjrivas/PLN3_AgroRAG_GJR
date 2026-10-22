import secrets
from dataclasses import asdict
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Query

from agro_rag.api.schemas import QueryRequest, QueryResponse
from agro_rag.application.query import BudgetExceeded, QueryService, UpstreamError
from agro_rag.application.retrieval import Retriever
from agro_rag.domain.evidence import Catalogue, Evidence


def public_evidence(evidence: Evidence) -> dict[str, Any]:
    result = asdict(evidence)
    result.pop("original_text")
    return result


def error(status: int, code: str, message: str, retryable: bool = False) -> HTTPException:
    return HTTPException(
        status,
        detail={
            "error": {
                "code": code,
                "message": message,
                "request_id": str(uuid4()),
                "retryable": retryable,
            }
        },
    )


def query_router(
    key: str, catalogue: Catalogue | None, retriever: Retriever | None, service: QueryService | None
) -> APIRouter:
    router = APIRouter()
    active = 0

    def authorize(given: str | None) -> None:
        if not key or not given or not secrets.compare_digest(key.encode(), given.encode()):
            raise error(401, "UNAUTHORIZED", "Credencial de lectura inválida")

    @router.get("/v1/corpus")
    def corpus(x_api_key: Annotated[str | None, Header()] = None) -> dict[str, Any]:
        authorize(x_api_key)
        if catalogue is None:
            raise error(503, "NOT_READY", "Corpus no disponible")
        return {
            "corpus_version": catalogue.version,
            "evidence_count": len(catalogue.evidence),
            "mode": "lexical_preview",
            "sources": sorted({e.source_id for e in catalogue.evidence}),
        }

    @router.get("/v1/evidence/{evidence_id}")
    def evidence(
        evidence_id: str, corpus_version: str, x_api_key: Annotated[str | None, Header()] = None
    ) -> dict[str, Any]:
        authorize(x_api_key)
        if catalogue and catalogue.version == corpus_version:
            for item in catalogue.evidence:
                if item.evidence_id == evidence_id:
                    return public_evidence(item)
        raise error(404, "NOT_FOUND", "Evidencia o versión no disponible")

    @router.get("/v1/preview/search")
    def search(
        question: Annotated[str, Query(min_length=1, max_length=2000)],
        crop: str | None = None,
        x_api_key: Annotated[str | None, Header()] = None,
    ) -> dict[str, Any]:
        authorize(x_api_key)
        if crop not in (None, "tomato", "lettuce") or not question.strip():
            raise error(422, "INPUT_INVALID", "Consulta inválida")
        if retriever is None:
            raise error(503, "NOT_READY", "Corpus no disponible")
        return {
            "mode": "lexical_preview",
            "evidence": [public_evidence(item) for item in retriever.search(question, crop)],
        }

    @router.post("/v1/query", response_model=QueryResponse)
    async def query(
        request: QueryRequest, x_api_key: Annotated[str | None, Header()] = None
    ) -> dict[str, Any]:
        nonlocal active
        authorize(x_api_key)
        if service is None:
            raise error(503, "NOT_READY", "Corpus o modelo no configurado")
        if active >= 2:
            raise error(429, "BUSY", "Hay dos consultas en curso", True)
        active += 1
        try:
            context = request.context.model_dump(exclude_none=True) if request.context else {}
            if request.clarification_context:
                context["clarification_context"] = request.clarification_context.model_dump()
            return await service.run(request.question, request.crop, context)
        except TimeoutError as exc:
            raise error(504, "DEADLINE", "Tiempo de consulta agotado", True) from exc
        except BudgetExceeded as exc:
            raise error(429, "BUDGET", "Presupuesto de consulta agotado") from exc
        except UpstreamError as exc:
            raise error(
                502, "MODEL_INVALID", "El modelo no produjo una salida válida", True
            ) from exc
        finally:
            active -= 1

    return router
