from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT = ROOT / "scripts" / "preflight_single_host.sh"
ENV_EXAMPLE = ROOT / "infra" / "deploy" / "production.env.example"
CONTAINER_WORKFLOW = ROOT / ".github" / "workflows" / "containers.yml"


def test_single_host_preflight_fails_closed_before_compose_up() -> None:
    script = PREFLIGHT.read_text(encoding="utf-8")

    assert "set -eu" in script
    assert "uname -s" in script
    assert "docker version" in script
    assert "docker compose version" in script
    for variable in (
        "AGRO_API_IMAGE",
        "AGRO_UI_IMAGE",
        "AGRO_GATEWAY_IMAGE",
        "AGRO_CATALOGUE_VOLUME",
        "AGRO_DOMAIN",
        "AGRO_OPENAI_MODEL",
        "AGRO_SECRETS_DIR",
        "AGRO_RELEASE_VERSION",
        "AGRO_COMMIT_SHA",
    ):
        assert variable in script
    assert "@sha256:" in script
    assert "org.opencontainers.image.revision" in script
    assert "10001:10001" in script
    assert "10002:10002" in script
    assert "docker volume inspect" in script
    assert "reader_key openai_api_key gateway_auth" in script
    assert "400|600" in script
    assert "compose.production.yaml config --quiet" in script
    assert "cat " not in script
    assert "\nenv\n" not in script


def test_single_host_environment_template_has_only_placeholders() -> None:
    template = ENV_EXAMPLE.read_text(encoding="utf-8")

    for variable in (
        "AGRO_API_IMAGE",
        "AGRO_UI_IMAGE",
        "AGRO_GATEWAY_IMAGE",
        "AGRO_CATALOGUE_VOLUME",
        "AGRO_DOMAIN",
        "AGRO_OPENAI_MODEL",
        "AGRO_SECRETS_DIR",
        "AGRO_RELEASE_VERSION",
        "AGRO_COMMIT_SHA",
    ):
        assert f"{variable}=" in template
    assert "reader_key=" not in template.lower()
    assert "openai_api_key=" not in template.lower()
    assert "password=" not in template.lower()
    assert "<" in template and ">" in template


def test_container_ci_parses_the_linux_preflight_with_a_release_image() -> None:
    workflow = CONTAINER_WORKFLOW.read_text(encoding="utf-8")

    assert "name: Validate single-host preflight syntax" in workflow
    assert "scripts/preflight_single_host.sh:/tmp/preflight_single_host.sh:ro" in workflow
    assert "--entrypoint sh" in workflow
    assert "agrorag-gateway:ci -n /tmp/preflight_single_host.sh" in workflow
