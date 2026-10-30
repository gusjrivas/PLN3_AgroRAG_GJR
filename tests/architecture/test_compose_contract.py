import json
import os
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _compose_config(*files: str, extra_env: dict[str, str] | None = None) -> dict[str, Any]:
    command = ["docker", "compose", "--profile", "admin"]
    for file in files:
        command.extend(("-f", file))
    command.extend(("config", "--format", "json"))
    environment = os.environ.copy()
    environment["AGRO_READER_KEY"] = "compose-test-reader-key-123456"
    environment.update(extra_env or {})
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def _mount(service: dict[str, Any], target: str) -> dict[str, Any]:
    return next(item for item in service["volumes"] if item["target"] == target)


def test_cmp_v2_base_and_dev_define_http_only_runtime_and_admin_job() -> None:
    config = _compose_config("compose.yaml", "compose.dev.yaml")
    services = config["services"]

    assert {"api", "ui", "catalogue-admin"}.issubset(services)
    assert services["api"]["build"]["target"] == "api"
    assert services["ui"]["build"]["target"] == "ui"
    assert services["ui"]["environment"]["AGRO_API_URL"] == "http://api:8000"
    assert services["ui"]["depends_on"]["api"]["condition"] == "service_healthy"
    assert services["catalogue-admin"]["profiles"] == ["admin"]
    assert services["catalogue-admin"]["command"][0:2] == ["agro-rag", "ingest"]


def test_dat_v2_api_catalogue_is_read_only_and_admin_is_read_write() -> None:
    config = _compose_config("compose.yaml", "compose.dev.yaml")
    services = config["services"]
    target = "/var/lib/agrorag/catalogue"

    assert _mount(services["api"], target)["read_only"] is True
    assert _mount(services["catalogue-admin"], target).get("read_only", False) is False
    assert config["volumes"]["catalogue"]["name"] == "agrorag_catalogue"


def test_cmp_v2_dev_publishes_loopback_only_and_has_healthchecks() -> None:
    config = _compose_config("compose.yaml", "compose.dev.yaml")
    services = config["services"]

    api_port = services["api"]["ports"][0]
    ui_port = services["ui"]["ports"][0]
    assert (api_port["host_ip"], api_port["published"], api_port["target"]) == (
        "127.0.0.1",
        "8000",
        8000,
    )
    assert (ui_port["host_ip"], ui_port["published"], ui_port["target"]) == (
        "127.0.0.1",
        "8501",
        8501,
    )
    assert services["api"]["healthcheck"]["test"] == ["CMD", "agro-rag-healthcheck"]
    assert services["ui"]["healthcheck"]["test"][0:2] == ["CMD", "python"]


def test_sec_v2_production_exposes_only_gateway_and_uses_immutable_images(tmp_path: Path) -> None:
    secrets = tmp_path / "secrets"
    secrets.mkdir()
    (secrets / "reader_key").write_text("test-reader", encoding="utf-8")
    (secrets / "openai_api_key").write_text("test-openai", encoding="utf-8")
    (secrets / "gateway_auth").write_text("agrorag test-hash", encoding="utf-8")
    config = _compose_config(
        "compose.yaml",
        "compose.production.yaml",
        extra_env={
            "AGRO_API_IMAGE": "registry.example/agro-api@sha256:" + "a" * 64,
            "AGRO_UI_IMAGE": "registry.example/agro-ui@sha256:" + "b" * 64,
            "AGRO_GATEWAY_IMAGE": "registry.example/agro-gateway@sha256:" + "c" * 64,
            "AGRO_CATALOGUE_VOLUME": "agrorag_catalogue_production_test",
            "AGRO_DOMAIN": "agrorag.example.test",
            "AGRO_OPENAI_MODEL": "test-model",
            "AGRO_SECRETS_DIR": str(secrets),
        },
    )
    services = config["services"]

    assert set(services) == {"api", "gateway", "ui"}
    assert "build" not in services["api"]
    assert "build" not in services["ui"]
    assert services["api"]["image"].endswith("a" * 64)
    assert services["ui"]["image"].endswith("b" * 64)
    assert "@sha256:" in services["gateway"]["image"]
    assert "ports" not in services["api"]
    assert "ports" not in services["ui"]
    assert {port["target"] for port in services["gateway"]["ports"]} == {80, 443}
    assert all(
        mount["type"] != "bind"
        for service in services.values()
        for mount in service.get("volumes", [])
    )


def test_sec_v2_production_limits_secrets_and_privileges(tmp_path: Path) -> None:
    secrets = tmp_path / "secrets"
    secrets.mkdir()
    for name in ("reader_key", "openai_api_key", "gateway_auth"):
        (secrets / name).write_text("synthetic", encoding="utf-8")
    config = _compose_config(
        "compose.yaml",
        "compose.production.yaml",
        extra_env={
            "AGRO_API_IMAGE": "registry.example/agro-api@sha256:" + "a" * 64,
            "AGRO_UI_IMAGE": "registry.example/agro-ui@sha256:" + "b" * 64,
            "AGRO_GATEWAY_IMAGE": "registry.example/agro-gateway@sha256:" + "c" * 64,
            "AGRO_CATALOGUE_VOLUME": "agrorag_catalogue_production_test",
            "AGRO_DOMAIN": "agrorag.example.test",
            "AGRO_OPENAI_MODEL": "test-model",
            "AGRO_SECRETS_DIR": str(secrets),
        },
    )
    api, ui, gateway = (config["services"][name] for name in ("api", "ui", "gateway"))

    assert {secret["source"] for secret in api["secrets"]} == {
        "openai_api_key",
        "reader_key",
    }
    assert {secret["source"] for secret in ui["secrets"]} == {"reader_key"}
    assert {secret["source"] for secret in gateway["secrets"]} == {"gateway_auth"}
    assert api["environment"]["AGRO_READER_KEY_FILE"] == "/run/secrets/reader_key"
    assert ui["environment"]["AGRO_READER_KEY_FILE"] == "/run/secrets/reader_key"
    assert api["environment"]["OPENAI_API_KEY_FILE"] == "/run/secrets/openai_api_key"
    for service in (api, ui, gateway):
        assert service["read_only"] is True
        assert service["cap_drop"] == ["ALL"]
        assert "no-new-privileges:true" in service["security_opt"]
        assert service["pids_limit"] > 0
        assert int(service["mem_limit"]) > 0
    assert api["environment"]["AGRO_HEALTHCHECK_EXPECTED_STATUS"] == "ready"
    rendered = json.dumps(config)
    assert "synthetic" not in rendered
