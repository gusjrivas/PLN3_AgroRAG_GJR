from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from agro_rag.api.health import router
from agro_rag.api.query import error, query_router
from agro_rag.application.query import QueryService
from agro_rag.bootstrap.settings import Settings
from agro_rag.domain.evidence import Catalogue
from agro_rag.infrastructure.audit import LoggingAuditSink
from agro_rag.infrastructure.corpus import load_catalogue
from agro_rag.infrastructure.ollama import OllamaModel
from agro_rag.infrastructure.retrieval import LexicalRetriever


def create_app(
    settings: Settings | None = None,
    *,
    catalogue: Catalogue | None = None,
    service: QueryService | None = None,
) -> FastAPI:
    config = settings or Settings()
    if catalogue is None and (config.catalogue_path / "active.json").exists():
        catalogue = load_catalogue(config.catalogue_path)
    retriever = LexicalRetriever(catalogue) if catalogue else None
    client = httpx.AsyncClient(trust_env=False)
    model = OllamaModel(client, config.ollama_url, config.model) if config.model else None
    if service is None and retriever and catalogue and model:
        service = QueryService(
            retriever,
            model,
            catalogue.version,
            audit_sink=LoggingAuditSink(),
        )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield
        await client.aclose()

    app = FastAPI(title="AgroRAG", version="0.1.0", lifespan=lifespan)
    app.include_router(router)
    app.include_router(query_router(config.reader_key, catalogue, retriever, service))

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

    return app
