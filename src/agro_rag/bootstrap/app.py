import json
import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import perf_counter
from typing import Annotated
from uuid import uuid4

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import RequestResponseEndpoint

from agro_rag.api.health import router
from agro_rag.api.query import error, query_router
from agro_rag.application.query import QueryService
from agro_rag.bootstrap.retrieval import build_retrieval_runtime
from agro_rag.bootstrap.settings import Settings
from agro_rag.domain.evidence import Catalogue
from agro_rag.infrastructure.audit import LoggingAuditSink
from agro_rag.infrastructure.corpus import load_catalogue
from agro_rag.infrastructure.ollama import OllamaModel
from agro_rag.infrastructure.openai import OpenAIModel


def _http_logger() -> logging.Logger:
    logger = logging.getLogger("agro_rag.http")
    if not any(getattr(handler, "agro_json", False) for handler in logger.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))
        handler.agro_json = True  # type: ignore[attr-defined]
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


def build_model(config: Settings, client: httpx.AsyncClient) -> OllamaModel | OpenAIModel | None:
    if config.model_provider == "openai":
        if config.openai_api_key is None or not config.openai_model:
            return None
        return OpenAIModel(
            client,
            config.openai_url,
            config.openai_api_key.get_secret_value(),
            config.openai_model,
        )
    return OllamaModel(client, config.ollama_url, config.model) if config.model else None


def create_app(
    settings: Settings | None = None,
    *,
    catalogue: Catalogue | None = None,
    service: QueryService | None = None,
) -> FastAPI:
    config = settings or Settings()
    http_logger = _http_logger()
    if catalogue is None and (config.catalogue_path / "active.json").exists():
        catalogue = load_catalogue(config.catalogue_path)
    retrieval_runtime = build_retrieval_runtime(config, catalogue) if catalogue else None
    retriever = retrieval_runtime.retriever if retrieval_runtime else None
    client = httpx.AsyncClient(trust_env=False)
    model = build_model(config, client) if service is None else None
    if service is None and retriever and catalogue and model:
        assert retrieval_runtime is not None
        service = QueryService(
            retriever,
            model,
            catalogue.version,
            audit_sink=LoggingAuditSink(),
            retrieval_mode=retrieval_runtime.mode,
        )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            await client.aclose()
            if retrieval_runtime is not None:
                retrieval_runtime.close()

    app = FastAPI(title="AgroRAG", version=config.release_version, lifespan=lifespan)

    @app.middleware("http")
    async def structured_http_log(request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid4())
        started = perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            payload = {
                "event": "http_request_completed",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": max(0, round((perf_counter() - started) * 1000)),
            }
            http_logger.info(json.dumps(payload, ensure_ascii=True, separators=(",", ":")))

    app.include_router(router)
    app.include_router(
        query_router(
            config.reader_key,
            catalogue,
            retriever,
            service,
            retrieval_runtime.mode if retrieval_runtime else config.retrieval_mode,
        )
    )

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    @app.exception_handler(RequestValidationError)
    async def input_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422, content=error(422, "INPUT_INVALID", "Entrada inválida").detail
        )

    @app.get("/health/ready")
    async def ready(x_api_key: Annotated[str | None, Header()] = None) -> dict[str, str]:
        import secrets

        if (
            not config.reader_key
            or not x_api_key
            or not secrets.compare_digest(config.reader_key.encode(), x_api_key.encode())
        ):
            raise error(401, "UNAUTHORIZED", "Credencial de lectura inválida")
        if service is None or (model is not None and not await model.ready()):
            raise error(503, "NOT_READY", "Corpus o modelo no disponible")
        return {"status": "ready"}

    @app.get("/health/version")
    async def version() -> dict[str, str | None]:
        return {
            "version": config.release_version,
            "commit": config.commit_sha,
            "image_digest": config.image_digest,
            "corpus_version": catalogue.version if catalogue is not None else None,
        }

    return app
