from pathlib import Path

import pytest
from pydantic import ValidationError

from agro_rag.bootstrap.settings import Settings
from agro_rag_ui.app import UISettings


def _isolated_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    for name in (
        "AGRO_READER_KEY",
        "AGRO_READER_KEY_FILE",
        "OPENAI_API_KEY",
        "OPENAI_API_KEY_FILE",
        "PINECONE_API_KEY",
        "PINECONE_API_KEY_FILE",
        "AGRO_API_URL",
    ):
        monkeypatch.delenv(name, raising=False)


def test_backend_loads_mounted_secret_files_and_redacts_values(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _isolated_settings(monkeypatch, tmp_path)
    reader = tmp_path / "reader_key"
    openai = tmp_path / "openai_api_key"
    pinecone = tmp_path / "pinecone_api_key"
    reader.write_text("reader-from-file-123456\n", encoding="utf-8")
    openai.write_text("openai-from-file-123456\n", encoding="utf-8")
    pinecone.write_text("pinecone-from-file-123456\n", encoding="utf-8")
    monkeypatch.setenv("AGRO_READER_KEY_FILE", str(reader))
    monkeypatch.setenv("OPENAI_API_KEY_FILE", str(openai))
    monkeypatch.setenv("PINECONE_API_KEY_FILE", str(pinecone))

    settings = Settings()

    assert settings.reader_key == "reader-from-file-123456"
    assert settings.openai_api_key is not None
    assert settings.openai_api_key.get_secret_value() == "openai-from-file-123456"
    assert settings.pinecone_api_key is not None
    assert settings.pinecone_api_key.get_secret_value() == "pinecone-from-file-123456"
    rendered = repr(settings)
    assert "reader-from-file" not in rendered
    assert "openai-from-file" not in rendered
    assert "pinecone-from-file" not in rendered


def test_backend_rejects_direct_and_file_secret_without_leaking_values(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _isolated_settings(monkeypatch, tmp_path)
    secret_file = tmp_path / "reader_key"
    secret_file.write_text("file-secret-sentinel-123456", encoding="utf-8")
    monkeypatch.setenv("AGRO_READER_KEY", "direct-secret-sentinel-123456")
    monkeypatch.setenv("AGRO_READER_KEY_FILE", str(secret_file))

    with pytest.raises(ValidationError) as raised:
        Settings()

    message = str(raised.value)
    assert "AGRO_READER_KEY" in message
    assert "AGRO_READER_KEY_FILE" in message
    assert "direct-secret-sentinel" not in message
    assert "file-secret-sentinel" not in message


@pytest.mark.parametrize("contents", [None, "", "   \n"])
def test_backend_rejects_missing_or_empty_secret_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, contents: str | None
) -> None:
    _isolated_settings(monkeypatch, tmp_path)
    secret_file = tmp_path / "reader_key"
    if contents is not None:
        secret_file.write_text(contents, encoding="utf-8")
    monkeypatch.setenv("AGRO_READER_KEY_FILE", str(secret_file))

    with pytest.raises(ValidationError) as raised:
        Settings()

    assert "AGRO_READER_KEY_FILE" in str(raised.value)


def test_ui_loads_reader_key_file_and_internal_api_url(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _isolated_settings(monkeypatch, tmp_path)
    secret_file = tmp_path / "reader_key"
    secret_file.write_text("ui-reader-from-file-123456\n", encoding="utf-8")
    monkeypatch.setenv("AGRO_READER_KEY_FILE", str(secret_file))
    monkeypatch.setenv("AGRO_API_URL", "http://api:8000")

    settings = UISettings()

    assert settings.reader_key == "ui-reader-from-file-123456"
    assert settings.api_url == "http://api:8000"
    assert "ui-reader-from-file" not in repr(settings)
