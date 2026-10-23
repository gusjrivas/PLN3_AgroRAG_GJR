from pydantic import SecretStr

from agro_rag.bootstrap.settings import Settings


def test_pinecone_key_is_loaded_from_process_environment_and_redacted(
    monkeypatch, tmp_path
) -> None:
    secret = "test-pinecone-process-only-123456789"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PINECONE_API_KEY", secret)

    settings = Settings()

    assert isinstance(settings.pinecone_api_key, SecretStr)
    assert settings.pinecone_api_key.get_secret_value() == secret
    assert secret not in repr(settings)


def test_process_environment_overrides_pinecone_key_from_ignored_dotenv(
    monkeypatch, tmp_path
) -> None:
    dotenv_secret = "test-pinecone-dotenv-123456789"
    process_secret = "test-pinecone-process-987654321"
    (tmp_path / ".env").write_text(
        f"PINECONE_API_KEY={dotenv_secret}\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PINECONE_API_KEY", process_secret)

    settings = Settings()

    assert settings.pinecone_api_key is not None
    assert settings.pinecone_api_key.get_secret_value() == process_secret
    assert dotenv_secret not in repr(settings)
    assert process_secret not in repr(settings)


def test_pinecone_key_can_be_loaded_from_ignored_dotenv(monkeypatch, tmp_path) -> None:
    secret = "test-pinecone-dotenv-only-123456789"
    (tmp_path / ".env").write_text(
        f"PINECONE_API_KEY={secret}\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PINECONE_API_KEY", raising=False)

    settings = Settings()

    assert settings.pinecone_api_key is not None
    assert settings.pinecone_api_key.get_secret_value() == secret
    assert secret not in repr(settings)


def test_blank_pinecone_key_is_treated_as_unconfigured(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PINECONE_API_KEY", "")

    assert Settings().pinecone_api_key is None
