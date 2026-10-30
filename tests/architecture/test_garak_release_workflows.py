import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER_WORKFLOW = ROOT / ".github" / "workflows" / "garak-runner.yml"
SCAN_WORKFLOW = ROOT / ".github" / "workflows" / "staging-security.yml"


def _uses(workflow: str) -> list[str]:
    return re.findall(r"uses:\s+([^\s#]+)", workflow)


def test_runner_workflow_builds_scans_then_publishes_one_immutable_image() -> None:
    workflow = RUNNER_WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow
    assert "pull_request:" not in workflow
    assert "docker build -f Dockerfile.garak" in workflow
    assert "anchore/sbom-action@" in workflow
    assert "aquasecurity/trivy-action@" in workflow
    assert "garak-runner=artifacts/garak-runner-trivy.json" in workflow
    assert "garak-runner-vulnerability-exceptions.json" in workflow
    publication = workflow[workflow.index("name: Publish immutable runner") :]
    assert "sha-${GITHUB_SHA}" in publication
    assert "docker build" not in publication
    assert ":latest" not in workflow
    assert "garak-runner-manifest.json" in publication


def test_authorized_staging_scan_requires_digest_files_and_encrypted_raw_evidence() -> None:
    workflow = SCAN_WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow
    assert "authorization_confirmed" in workflow
    assert "environment: staging-security" in workflow
    assert "@sha256:" in workflow
    assert "GARAK_GATEWAY_AUTHORIZATION" in workflow
    assert "GARAK_READER_KEY" in workflow
    assert "GARAK_REPORT_ENCRYPTION_KEY" in workflow
    assert "gateway_authorization" in workflow
    assert "reader_key" in workflow
    assert "docker compose -f compose.security.yaml" in workflow
    assert "--no-build" in workflow
    assert "openssl enc -aes-256-cbc" in workflow
    assert "garak-raw-encrypted" in workflow
    assert "retention-days: 7" in workflow
    assert "garak-summary" in workflow
    assert "retention-days: 90" in workflow
    assert "if: always()" in workflow
    assert 'sudo rm -rf -- "$SCAN_ROOT"' in workflow

    upload_blocks = workflow.split("uses: actions/upload-artifact@")
    assert all("/raw/" not in block for block in upload_blocks[1:])


def test_new_workflows_pin_every_third_party_action_to_a_full_commit() -> None:
    values = [
        value
        for path in (RUNNER_WORKFLOW, SCAN_WORKFLOW)
        for value in _uses(path.read_text(encoding="utf-8"))
    ]

    assert values
    assert all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", value) for value in values)
