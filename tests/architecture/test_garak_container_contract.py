from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_garak_is_a_pinned_separate_one_shot_profile() -> None:
    dockerfile = (ROOT / "Dockerfile.garak").read_text(encoding="utf-8")
    compose = (ROOT / "compose.security.yaml").read_text(encoding="utf-8")
    lock = (ROOT / "infra" / "garak" / "requirements.lock").read_text(encoding="utf-8")

    assert "garak==0.17.0" in dockerfile
    assert "garak==0.17.0" in lock
    assert "filelock==4.2.1" in lock
    assert len(lock.splitlines()) == 197
    assert 'TARGETARCH" = "amd64"' in dockerfile
    assert "profiles: [security]" in compose
    assert 'restart: "no"' in compose
    assert "ports:" not in compose
    assert "gateway_authorization" in compose
    assert "reader_key" in compose
    assert "cap_drop: [ALL]" in compose
    assert "no-new-privileges:true" in compose


def test_garak_configuration_is_bounded_reproducible_and_black_box() -> None:
    config = (ROOT / "infra" / "garak" / "garak.yaml").read_text(encoding="utf-8")
    gateway = (ROOT / "infra" / "gateway" / "Caddyfile").read_text(encoding="utf-8")

    assert "seed: 1729" in config
    assert "generations: 1" in config
    assert "soft_probe_prompt_cap: 32" in config
    assert "target_type: rest" in config
    assert "http://127.0.0.1:8090/generate" in config
    assert "handle /v1/*" in gateway
    assert "reverse_proxy api:8000" in gateway


def test_raw_garak_reports_are_never_versioned() -> None:
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "output/garak/raw/" in ignore


def test_garak_vulnerability_exception_is_isolated_from_product_policy() -> None:
    exceptions = ROOT / "configs" / "security" / "garak-runner-vulnerability-exceptions.json"
    content = exceptions.read_text(encoding="utf-8")

    assert '"component": "garak-runner"' in content
    assert "CVE-2026-104851" in content
    assert "gateway" not in content
