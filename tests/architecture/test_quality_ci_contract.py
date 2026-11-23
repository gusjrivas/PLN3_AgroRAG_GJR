from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def test_optional_tracing_is_audited_and_included_in_coverage() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    tracing = workflow[
        workflow.index("name: Verify optional tracing contract") : workflow.index("  specs:")
    ]

    assert "--cov --cov-append" in tracing
    assert "python -m pip_audit --skip-editable" in tracing
