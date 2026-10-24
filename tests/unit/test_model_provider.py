import asyncio

import httpx


def test_openai_provider_requires_key_and_model():
    from agro_rag.bootstrap.app import build_model
    from agro_rag.bootstrap.settings import Settings
    from agro_rag.infrastructure.openai import OpenAIModel

    client = httpx.AsyncClient()
    try:
        configured = Settings(
            model_provider="openai",
            openai_api_key="secret",
            openai_model="gpt-test",
        )
        assert isinstance(build_model(configured, client), OpenAIModel)
        assert (
            build_model(
                Settings(
                    model_provider="openai",
                    openai_api_key=None,
                    openai_model="gpt-test",
                ),
                client,
            )
            is None
        )
        assert (
            build_model(
                Settings(model_provider="openai", openai_api_key="secret", openai_model=""),
                client,
            )
            is None
        )
    finally:
        asyncio.run(client.aclose())


def test_openai_key_is_redacted_from_settings_repr():
    from agro_rag.bootstrap.settings import Settings

    settings = Settings(openai_api_key="super-secret-openai-key")

    assert "super-secret-openai-key" not in repr(settings)


def test_ollama_remains_an_explicit_provider():
    from agro_rag.bootstrap.app import build_model
    from agro_rag.bootstrap.settings import Settings
    from agro_rag.infrastructure.ollama import OllamaModel

    client = httpx.AsyncClient()
    try:
        model = build_model(Settings(model_provider="ollama", model="qwen2.5:1.5b"), client)
        assert isinstance(model, OllamaModel)
    finally:
        asyncio.run(client.aclose())
