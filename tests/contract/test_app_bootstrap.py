import builtins
from typing import Any

import pytest
from fastapi.testclient import TestClient

from agro_rag.application.query import QueryService
from agro_rag.bootstrap.app import create_app
from agro_rag.bootstrap.settings import Settings

KEY = "reader-secret"
TRACING_MODULE = "agro_rag.infrastructure.tracing"


class _Retriever:
    def search(self, question: str, filters: Any) -> tuple[()]:
        return ()


class _Model:
    def __init__(self, ready: bool) -> None:
        self._ready = ready

    async def generate(self, role: str, payload: Any, timeout: Any) -> Any:
        raise AssertionError("readiness must not generate")

    async def ready(self) -> bool:
        return self._ready


def _settings(**overrides: Any) -> Settings:
    return Settings(_env_file=None, reader_key=KEY, **overrides)


def test_ready_reports_ready_when_service_is_injected() -> None:
    service = QueryService(_Retriever(), _Model(True), "v1")
    with TestClient(create_app(_settings(), service=service)) as client:
        response = client.get("/health/ready", headers={"X-API-Key": KEY})
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_ready_rejects_wrong_key_and_missing_service() -> None:
    with TestClient(create_app(_settings())) as client:
        assert client.get("/health/ready", headers={"X-API-Key": "bad"}).status_code == 401
        assert client.get("/health/ready", headers={"X-API-Key": KEY}).status_code == 503


def _block_tracing_import(monkeypatch: pytest.MonkeyPatch, missing: str) -> None:
    real_import = builtins.__import__

    def fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == TRACING_MODULE:
            raise ModuleNotFoundError(f"No module named {missing!r}", name=missing)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)


def test_enabled_tracing_without_extra_fails_with_actionable_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = create_app(_settings(tracing_enabled=True))
    _block_tracing_import(monkeypatch, "opentelemetry")
    with pytest.raises(RuntimeError, match="uv sync --extra tracing"):
        with TestClient(app):
            pass


def test_enabled_tracing_does_not_mask_unrelated_missing_modules(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = create_app(_settings(tracing_enabled=True))
    _block_tracing_import(monkeypatch, "something_else")
    with pytest.raises(ModuleNotFoundError, match="something_else"):
        with TestClient(app):
            pass


def test_build_model_selects_provider_and_requires_openai_configuration() -> None:
    import httpx
    from pydantic import SecretStr

    from agro_rag.bootstrap.app import build_model
    from agro_rag.infrastructure.ollama import OllamaModel
    from agro_rag.infrastructure.openai import OpenAIModel

    client = httpx.AsyncClient(trust_env=False)
    assert build_model(_settings(), client) is None
    assert isinstance(build_model(_settings(model="llama"), client), OllamaModel)
    assert build_model(_settings(model_provider="openai"), client) is None
    configured = _settings(
        model_provider="openai", openai_api_key=SecretStr("k"), openai_model="gpt"
    )
    assert isinstance(build_model(configured, client), OpenAIModel)
