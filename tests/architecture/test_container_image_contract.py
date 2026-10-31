import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _dockerfile() -> str:
    return (ROOT / "Dockerfile").read_text(encoding="utf-8")


def test_img_v2_has_builder_and_separate_non_root_runtime_targets() -> None:
    dockerfile = _dockerfile()
    stages = set(re.findall(r"^FROM\s+\S+(?:\s+AS\s+(\S+))?", dockerfile, re.MULTILINE | re.I))

    assert {"builder", "runtime", "api", "ui"}.issubset(stages)
    assert dockerfile.count("@sha256:") >= 2
    assert "uv sync --frozen --no-dev --no-editable" in dockerfile
    assert dockerfile.count("USER 10001:10001") >= 2

    commands = [
        json.loads(value) for value in re.findall(r"^CMD\s+(\[.*\])$", dockerfile, re.MULTILINE)
    ]
    assert any(
        command[0] == "uvicorn" and "--factory" in command and "--no-access-log" in command
        for command in commands
    )
    assert any(command[:2] == ["streamlit", "run"] for command in commands)


def test_img_v2_uses_oci_labels_and_never_declares_secret_build_inputs() -> None:
    dockerfile = _dockerfile()

    assert "org.opencontainers.image.revision" in dockerfile
    assert "org.opencontainers.image.version" in dockerfile
    assert "AGRO_RELEASE_VERSION=${APP_VERSION}" in dockerfile
    assert "AGRO_COMMIT_SHA=${VCS_REF}" in dockerfile
    assert not re.search(
        r"^(?:ARG|ENV)\s+.*(?:API_KEY|READER_KEY|SECRET|TOKEN)",
        dockerfile,
        re.MULTILINE | re.IGNORECASE,
    )
    assert "caddy:2.11.7-alpine@sha256:" in dockerfile
    assert "apk upgrade --no-cache" in dockerfile


def test_gateway_v2_carries_the_same_release_identity_as_api_and_ui() -> None:
    dockerfile = _dockerfile()
    gateway = dockerfile.split("FROM ${CADDY_IMAGE} AS gateway", maxsplit=1)[1]

    assert "ARG APP_VERSION=0.1.0" in gateway
    assert "ARG VCS_REF=unknown" in gateway
    assert 'org.opencontainers.image.version="${APP_VERSION}"' in gateway
    assert 'org.opencontainers.image.revision="${VCS_REF}"' in gateway


def test_img_v2_build_context_excludes_private_and_development_artifacts() -> None:
    patterns = {
        line.strip()
        for line in (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert {
        ".git",
        ".env*",
        ".venv",
        "tests",
        "output",
        "data/raw",
        "data/processed",
        "docs/evidence/workbooks",
    }.issubset(patterns)
