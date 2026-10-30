import json
from datetime import date
from pathlib import Path

from scripts.check_garak_policy import evaluate_report


def _write(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _report(path: Path) -> Path:
    rows = [
        {"entry_type": "attempt", "prompt": "SECRET-PROMPT", "output": "SECRET-OUTPUT"},
        {
            "entry_type": "eval",
            "probe": "promptinject.HijackHateHumans",
            "detector": "promptinject.AttackRogueString",
            "passed": 3,
            "fails": 1,
            "nones": 0,
            "total_evaluated": 4,
            "total_processed": 4,
        },
    ]
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    return path


def _policy(path: Path) -> Path:
    return _write(
        path,
        {
            "schema_version": 1,
            "rules": [
                {
                    "probe": "promptinject.HijackHateHumans",
                    "detector": "promptinject.AttackRogueString",
                    "severity": "high",
                    "max_regression": 0.0,
                }
            ],
        },
    )


def test_high_finding_without_triage_blocks_and_summary_is_sanitized(tmp_path: Path) -> None:
    result = evaluate_report(_report(tmp_path / "raw.jsonl"), _policy(tmp_path / "policy.json"))

    assert result["approved"] is False
    assert "untriaged_high" in result["blocking_reasons"]
    serialized = json.dumps(result)
    assert "SECRET-PROMPT" not in serialized
    assert "SECRET-OUTPUT" not in serialized


def test_confirmed_high_requires_complete_unexpired_exception(tmp_path: Path) -> None:
    report = _report(tmp_path / "raw.jsonl")
    policy = _policy(tmp_path / "policy.json")
    triage = _write(
        tmp_path / "triage.json",
        {
            "schema_version": 1,
            "findings": [
                {
                    "probe": "promptinject.HijackHateHumans",
                    "detector": "promptinject.AttackRogueString",
                    "status": "confirmed",
                    "reviewer": "security-reviewer",
                    "reviewed_at": "2026-10-30",
                }
            ],
        },
    )
    exceptions = _write(
        tmp_path / "exceptions.json",
        {
            "schema_version": 1,
            "exceptions": [
                {
                    "probe": "promptinject.HijackHateHumans",
                    "detector": "promptinject.AttackRogueString",
                    "owner": "Gustavo",
                    "risk": "PoC acotada",
                    "tracking": "MR #30",
                    "expires": "2026-11-15",
                }
            ],
        },
    )

    approved = evaluate_report(
        report,
        policy,
        triage_path=triage,
        exceptions_path=exceptions,
        today=date(2026, 10, 30),
    )
    expired = evaluate_report(
        report,
        policy,
        triage_path=triage,
        exceptions_path=exceptions,
        today=date(2026, 11, 16),
    )

    assert approved["approved"] is True
    assert expired["approved"] is False
    assert "confirmed_high" in expired["blocking_reasons"]


def test_regression_over_versioned_baseline_blocks(tmp_path: Path) -> None:
    baseline = _write(
        tmp_path / "baseline.json",
        {
            "schema_version": 1,
            "results": [
                {
                    "probe": "promptinject.HijackHateHumans",
                    "detector": "promptinject.AttackRogueString",
                    "failure_rate": 0.10,
                }
            ],
        },
    )
    result = evaluate_report(
        _report(tmp_path / "raw.jsonl"),
        _policy(tmp_path / "policy.json"),
        baseline_path=baseline,
    )

    assert result["approved"] is False
    assert "regression" in result["blocking_reasons"]
