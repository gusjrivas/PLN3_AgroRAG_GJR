import json
import os
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _compose_config(*files: str) -> dict[str, Any]:
    command = ["docker", "compose", "--profile", "admin"]
    for file in files:
        command.extend(("-f", file))
    command.extend(("config", "--format", "json"))
    environment = os.environ.copy()
    environment["AGRO_READER_KEY"] = "compose-test-reader-key-123456"
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
