import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "containers.yml"


def test_ci_v2_builds_once_tests_the_images_and_emits_supply_chain_evidence() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "docker build --target api" in workflow
    assert "docker build --target ui" in workflow
    assert "docker build --target gateway" in workflow
    assert "tests/e2e/test_compose_browser.py" in workflow
    assert "anchore/sbom-action@" in workflow
    assert "aquasecurity/trivy-action@" in workflow
    assert "severity: CRITICAL,HIGH" in workflow
    assert "scripts/check_vulnerability_policy.py" in workflow
    assert "exit-code: '0'" in workflow
    assert "release-manifest.json" in workflow
    inspection = workflow[
        workflow.index("name: Inspect runtime identities") : workflow.index(
            "name: Validate single-host preflight syntax"
        )
    ]
    assert "org.opencontainers.image.revision" in inspection
    for image in ("agrorag-api:ci", "agrorag-ui:ci", "agrorag-gateway:ci"):
        assert image in inspection


def test_ci_v2_publishes_only_sha_and_semver_without_rebuild_or_latest() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    publication = workflow[workflow.index("name: Publish immutable images") :]

    assert "sha-${GITHUB_SHA}" in publication
    assert "GITHUB_REF_NAME" in publication
    assert "refs/tags/v" in publication
    assert ":latest" not in workflow
    assert "docker build" not in publication
    assert "docker push" in publication


def test_ci_v2_third_party_actions_are_pinned_to_full_commits() -> None:
    workflows = (ROOT / ".github" / "workflows").glob("*.yml")
    uses = [
        value
        for path in workflows
        for value in re.findall(r"uses:\s+([^\s#]+)", path.read_text(encoding="utf-8"))
    ]

    assert uses
    assert all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", value) for value in uses)
