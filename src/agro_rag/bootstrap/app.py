from fastapi import FastAPI

from agro_rag.api.health import router


def create_app() -> FastAPI:
    app = FastAPI(title="AgroRAG", version="0.1.0")
    app.include_router(router)
    return app
