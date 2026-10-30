import json
import logging
from pathlib import Path

from fastapi.testclient import TestClient

from agro_rag.bootstrap.app import create_app
from agro_rag.bootstrap.settings import Settings


def test_ops_v2_release_identity_is_exposed_without_secrets(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        release_version="2.0.0-rc.1",
        commit_sha="a" * 40,
        image_digest="sha256:" + "b" * 64,
        catalogue_path=tmp_path,
    )

    with TestClient(create_app(settings)) as client:
        response = client.get("/health/version", headers={"Authorization": "sentinel-secret"})

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.0.0-rc.1",
        "commit": "a" * 40,
        "image_digest": "sha256:" + "b" * 64,
        "corpus_version": None,
    }
    assert "sentinel-secret" not in response.text


def test_ops_v2_http_log_is_json_and_omits_query_and_credentials(monkeypatch) -> None:
    messages: list[str] = []

    def capture_info(self, message: str, *args, **kwargs) -> None:
        if self.name == "agro_rag.http":
            messages.append(message)

    monkeypatch.setattr(logging.Logger, "info", capture_info)
    with TestClient(create_app(Settings(_env_file=None))) as client:
        response = client.get(
            "/health/live?token=sentinel-query",
            headers={"Authorization": "sentinel-header"},
        )

    assert len(messages) == 1
    payload = json.loads(messages[0])
    assert payload["event"] == "http_request_completed"
    assert payload["method"] == "GET"
    assert payload["path"] == "/health/live"
    assert payload["status_code"] == 200
    assert isinstance(payload["duration_ms"], int)
    assert payload["duration_ms"] >= 0
    assert len(payload["request_id"]) == 36
    assert response.headers["X-Request-ID"] == payload["request_id"]
    assert "sentinel-query" not in messages[0]
    assert "sentinel-header" not in messages[0]
