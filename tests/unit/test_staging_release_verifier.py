import json
from pathlib import Path

import httpx
import pytest

from scripts.verify_staging_release import (
    StagingVerificationError,
    load_release_manifest,
    verify_staging_release,
)

REPOSITORY = "gusjrivas/pln3_agrorag_gjr"
COMMIT = "a" * 40
API_IMAGE = f"ghcr.io/{REPOSITORY}/api@sha256:{'b' * 64}"


def _manifest(path: Path, **overrides: object) -> Path:
    payload: dict[str, object] = {
        "commit": COMMIT,
        "images": {
            "api": API_IMAGE,
            "ui": f"ghcr.io/{REPOSITORY}/ui@sha256:{'c' * 64}",
            "gateway": f"ghcr.io/{REPOSITORY}/gateway@sha256:{'d' * 64}",
        },
    }
    payload.update(overrides)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_staging_verifier_binds_live_identity_catalogue_and_functional_query(
    tmp_path: Path,
) -> None:
    manifest_path = _manifest(tmp_path / "release-manifest.json")
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path == "/health/version":
            return httpx.Response(
                200,
                json={
                    "version": "2.0.0-rc.1",
                    "commit": COMMIT,
                    "image_digest": API_IMAGE,
                    "corpus_version": "corpus-v1",
                },
            )
        if request.url.path == "/v1/corpus":
            return httpx.Response(
                200,
                json={
                    "corpus_version": "corpus-v1",
                    "evidence_count": 27,
                    "mode": "lexical_preview",
                    "sources": ["FAO", "INTA"],
                },
            )
        assert request.url.path == "/v1/query"
        assert json.loads(request.content) == {
            "question": "¿Qué evidencia describe el manejo del riego en tomate?",
            "crop": "tomato",
        }
        return httpx.Response(
            200,
            json={
                "request_id": "123e4567-e89b-42d3-a456-426614174000",
                "status": "answered",
                "corpus_version": "corpus-v1",
                "citations": [{"evidence_id": "ev-1"}],
            },
        )

    manifest = load_release_manifest(manifest_path, REPOSITORY)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        summary = verify_staging_release(
            manifest=manifest,
            manifest_path=manifest_path,
            base_url="https://staging.example.org",
            release_version="2.0.0-rc.1",
            corpus_version="corpus-v1",
            gateway_authorization="Basic c3RhZ2luZzpzZWNyZXQ=",
            reader_key="reader-secret",
            question="¿Qué evidencia describe el manejo del riego en tomate?",
            crop="tomato",
            client=client,
        )

    assert [request.url.path for request in seen] == [
        "/health/version",
        "/v1/corpus",
        "/v1/query",
    ]
    assert all(request.headers["Authorization"].startswith("Basic ") for request in seen)
    assert all(request.headers["X-API-Key"] == "reader-secret" for request in seen)
    assert summary["status"] == "approved"
    assert summary["release"]["commit"] == COMMIT
    assert summary["catalogue"] == {
        "corpus_version": "corpus-v1",
        "evidence_count": 27,
        "mode": "lexical_preview",
    }
    assert summary["functional_query"] == {
        "status": "answered",
        "request_id": "123e4567-e89b-42d3-a456-426614174000",
        "citation_count": 1,
    }
    serialized = json.dumps(summary)
    assert "reader-secret" not in serialized
    assert "c3RhZ2luZzpzZWNyZXQ" not in serialized
    assert "manejo del riego" not in serialized


@pytest.mark.parametrize(
    "payload",
    [
        {"commit": COMMIT, "images": {"api": "ghcr.io/repo/api:latest"}},
        {
            "commit": COMMIT,
            "images": {
                "api": API_IMAGE,
                "ui": f"ghcr.io/{REPOSITORY}/ui@sha256:{'c' * 64}",
                "gateway": f"ghcr.io/attacker/repo/gateway@sha256:{'d' * 64}",
            },
        },
        {"commit": COMMIT, "images": {}, "unexpected": True},
    ],
)
def test_release_manifest_rejects_tags_foreign_images_and_schema_drift(
    tmp_path: Path, payload: dict[str, object]
) -> None:
    path = tmp_path / "release-manifest.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(StagingVerificationError, match="Manifiesto de release inválido"):
        load_release_manifest(path, REPOSITORY)


def test_release_manifest_must_match_the_requested_commit(tmp_path: Path) -> None:
    path = _manifest(tmp_path / "release-manifest.json")

    with pytest.raises(StagingVerificationError, match="Manifiesto de release inválido"):
        load_release_manifest(path, REPOSITORY, "e" * 40)


@pytest.mark.parametrize(
    "base_url",
    [
        "http://staging.example.org",
        "https://user:password@staging.example.org",
        "https://staging.example.org/v1",
        "https://staging.example.org?token=secret",
    ],
)
def test_staging_verifier_rejects_non_origin_or_non_https_targets(
    tmp_path: Path, base_url: str
) -> None:
    manifest_path = _manifest(tmp_path / "release-manifest.json")
    manifest = load_release_manifest(manifest_path, REPOSITORY)

    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(500))) as client:
        with pytest.raises(StagingVerificationError, match="Target staging inválido"):
            verify_staging_release(
                manifest=manifest,
                manifest_path=manifest_path,
                base_url=base_url,
                release_version="2.0.0-rc.1",
                corpus_version="corpus-v1",
                gateway_authorization="Basic c2VjcmV0",
                reader_key="reader-secret",
                question="pregunta sintética",
                crop=None,
                client=client,
            )


def test_staging_verifier_rejects_redirect_without_leaking_response_or_credentials(
    tmp_path: Path,
) -> None:
    manifest_path = _manifest(tmp_path / "release-manifest.json")
    manifest = load_release_manifest(manifest_path, REPOSITORY)
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            302,
            headers={"Location": "https://attacker.example/reader-secret"},
            text="c3RhZ2luZzpzZWNyZXQ=",
        )
    )

    with httpx.Client(transport=transport, follow_redirects=False) as client:
        with pytest.raises(StagingVerificationError) as error:
            verify_staging_release(
                manifest=manifest,
                manifest_path=manifest_path,
                base_url="https://staging.example.org",
                release_version="2.0.0-rc.1",
                corpus_version="corpus-v1",
                gateway_authorization="Basic c3RhZ2luZzpzZWNyZXQ=",
                reader_key="reader-secret",
                question="pregunta sintética",
                crop=None,
                client=client,
            )

    assert "reader-secret" not in str(error.value)
    assert "c3RhZ2luZzpzZWNyZXQ" not in str(error.value)
    assert "attacker.example" not in str(error.value)
