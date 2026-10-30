"""Verify that a deployed staging target matches one immutable release manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

import httpx

COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")
DIGEST_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
REPOSITORY_PATTERN = re.compile(r"[a-z0-9_.-]+/[a-z0-9_.-]+")
SAFE_VALUE_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.+-]{0,127}")
BASIC_PATTERN = re.compile(r"Basic [A-Za-z0-9+/]+={0,2}")
HOSTNAME_PATTERN = re.compile(r"[A-Za-z0-9.-]+")


class StagingVerificationError(RuntimeError):
    """A sanitized release verification failure."""


@dataclass(frozen=True)
class ReleaseManifest:
    commit: str
    images: dict[str, str]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_release_manifest(
    path: Path, repository: str, expected_commit: str | None = None
) -> ReleaseManifest:
    """Load a strict product manifest and reject tags or foreign packages."""
    try:
        normalized_repository = repository.lower()
        if not REPOSITORY_PATTERN.fullmatch(normalized_repository):
            raise ValueError
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or set(payload) != {"commit", "images"}:
            raise ValueError
        commit = payload["commit"]
        images = payload["images"]
        if not isinstance(commit, str) or not COMMIT_PATTERN.fullmatch(commit):
            raise ValueError
        if expected_commit is not None and commit != expected_commit:
            raise ValueError
        if not isinstance(images, dict) or set(images) != {"api", "ui", "gateway"}:
            raise ValueError
        validated: dict[str, str] = {}
        for component in ("api", "ui", "gateway"):
            image = images[component]
            prefix = f"ghcr.io/{normalized_repository}/{component}@"
            if (
                not isinstance(image, str)
                or not image.startswith(prefix)
                or not DIGEST_PATTERN.fullmatch(image.removeprefix(prefix))
            ):
                raise ValueError
            validated[component] = image
        return ReleaseManifest(commit=commit, images=validated)
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise StagingVerificationError("Manifiesto de release inválido") from exc


def _validated_origin(value: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or not HOSTNAME_PATTERN.fullmatch(parsed.hostname)
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise StagingVerificationError("Target staging inválido")
    return value.rstrip("/")


def _validated_credentials(gateway_authorization: str, reader_key: str) -> dict[str, str]:
    if (
        not BASIC_PATTERN.fullmatch(gateway_authorization)
        or not reader_key
        or reader_key != reader_key.strip()
        or "\n" in reader_key
        or "\r" in reader_key
    ):
        raise StagingVerificationError("Credenciales de staging inválidas")
    return {"Authorization": gateway_authorization, "X-API-Key": reader_key}


def _request_json(
    client: httpx.Client,
    method: str,
    url: str,
    *,
    headers: dict[str, str],
    stage: str,
    payload: dict[str, str] | None = None,
) -> dict[str, Any]:
    try:
        response = client.request(method, url, headers=headers, json=payload)
    except httpx.HTTPError as exc:
        raise StagingVerificationError(f"Fallo de red en {stage}") from exc
    if response.status_code != 200:
        raise StagingVerificationError(
            f"Respuesta inválida en {stage}: HTTP {response.status_code}"
        )
    try:
        data = response.json()
    except (json.JSONDecodeError, UnicodeError, ValueError) as exc:
        raise StagingVerificationError(f"JSON inválido en {stage}") from exc
    if not isinstance(data, dict):
        raise StagingVerificationError(f"Contrato inválido en {stage}")
    return data


def verify_staging_release(
    *,
    manifest: ReleaseManifest,
    manifest_path: Path,
    base_url: str,
    release_version: str,
    corpus_version: str,
    gateway_authorization: str,
    reader_key: str,
    question: str,
    crop: str | None,
    client: httpx.Client,
) -> dict[str, Any]:
    """Probe identity, catalogue and one real query without retaining content."""
    origin = _validated_origin(base_url)
    if not SAFE_VALUE_PATTERN.fullmatch(release_version) or not SAFE_VALUE_PATTERN.fullmatch(
        corpus_version
    ):
        raise StagingVerificationError("Identidad esperada inválida")
    if not question.strip() or len(question) > 2000 or crop not in (None, "tomato", "lettuce"):
        raise StagingVerificationError("Consulta sintética inválida")
    if client.follow_redirects:
        raise StagingVerificationError("El cliente de verificación no debe seguir redirects")
    headers = _validated_credentials(gateway_authorization, reader_key)

    identity = _request_json(
        client,
        "GET",
        f"{origin}/health/version",
        headers=headers,
        stage="identidad",
    )
    expected_identity = {
        "version": release_version,
        "commit": manifest.commit,
        "image_digest": manifest.images["api"],
        "corpus_version": corpus_version,
    }
    if identity != expected_identity:
        raise StagingVerificationError("La identidad desplegada no coincide con el manifiesto")

    catalogue = _request_json(
        client,
        "GET",
        f"{origin}/v1/corpus",
        headers=headers,
        stage="catálogo",
    )
    evidence_count = catalogue.get("evidence_count")
    mode = catalogue.get("mode")
    if (
        catalogue.get("corpus_version") != corpus_version
        or not isinstance(evidence_count, int)
        or isinstance(evidence_count, bool)
        or evidence_count <= 0
        or not isinstance(mode, str)
        or not SAFE_VALUE_PATTERN.fullmatch(mode)
    ):
        raise StagingVerificationError("El catálogo desplegado no coincide con la release")

    request_payload = {"question": question.strip()}
    if crop is not None:
        request_payload["crop"] = crop
    result = _request_json(
        client,
        "POST",
        f"{origin}/v1/query",
        headers=headers,
        stage="consulta funcional",
        payload=request_payload,
    )
    citations = result.get("citations")
    request_id = result.get("request_id")
    try:
        normalized_request_id = str(UUID(request_id)) if isinstance(request_id, str) else ""
    except ValueError:
        normalized_request_id = ""
    if (
        result.get("status") != "answered"
        or result.get("corpus_version") != corpus_version
        or not normalized_request_id
        or not isinstance(citations, list)
        or not citations
    ):
        raise StagingVerificationError("La consulta funcional no produjo una respuesta citada")

    return {
        "schema_version": 1,
        "verified_at": datetime.now(UTC).isoformat(),
        "status": "approved",
        "target": {"hostname": urlsplit(origin).hostname},
        "release": {
            "version": release_version,
            "commit": manifest.commit,
            "images": manifest.images,
            "manifest_sha256": _sha256(manifest_path),
        },
        "catalogue": {
            "corpus_version": corpus_version,
            "evidence_count": evidence_count,
            "mode": mode,
        },
        "functional_query": {
            "status": "answered",
            "request_id": normalized_request_id,
            "citation_count": len(citations),
        },
    }


def _read_required(path: Path, label: str) -> str:
    try:
        value = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        raise StagingVerificationError(f"No se pudo leer {label}") from exc
    if not value:
        raise StagingVerificationError(f"{label} vacío")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--release-version", required=True)
    parser.add_argument("--corpus-version", required=True)
    parser.add_argument("--gateway-authorization-file", type=Path, required=True)
    parser.add_argument("--reader-key-file", type=Path, required=True)
    parser.add_argument("--question-file", type=Path, required=True)
    parser.add_argument("--crop", choices=("tomato", "lettuce"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        manifest = load_release_manifest(args.manifest, args.repository, args.expected_commit)
        with httpx.Client(timeout=30.0, follow_redirects=False, trust_env=False) as client:
            summary = verify_staging_release(
                manifest=manifest,
                manifest_path=args.manifest,
                base_url=args.base_url,
                release_version=args.release_version,
                corpus_version=args.corpus_version,
                gateway_authorization=_read_required(
                    args.gateway_authorization_file, "autorización gateway"
                ),
                reader_key=_read_required(args.reader_key_file, "reader key"),
                question=_read_required(args.question_file, "consulta sintética"),
                crop=args.crop,
                client=client,
            )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        args.output.chmod(0o600)
        print(json.dumps({"status": "approved", "evidence": str(args.output)}))
        return 0
    except StagingVerificationError as exc:
        blocked = {
            "schema_version": 1,
            "verified_at": datetime.now(UTC).isoformat(),
            "status": "blocked",
            "reason": str(exc),
        }
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(blocked, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            args.output.chmod(0o600)
        except OSError:
            pass
        print(json.dumps({"status": "blocked", "reason": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
