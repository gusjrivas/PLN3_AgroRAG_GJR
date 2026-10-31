import importlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def runner(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    sys.modules.pop("run_garak", None)
    return importlib.import_module("run_garak")


def test_runner_sets_private_umask_before_creating_evidence(
    runner, monkeypatch: pytest.MonkeyPatch
) -> None:
    observed: list[int] = []
    monkeypatch.setattr(runner.os, "umask", lambda mode: observed.append(mode) or 0o022)

    runner._set_private_umask()

    assert observed == [0o077]


@pytest.mark.skipif(os.name == "nt", reason="Windows no aplica bits POSIX al crear archivos")
def test_private_umask_protects_raw_from_its_first_byte(runner, tmp_path: Path) -> None:
    previous = os.umask(0o022)
    try:
        runner._set_private_umask()
        raw = tmp_path / "partial.report.jsonl"
        raw.touch()
        assert stat.S_IMODE(raw.stat().st_mode) == 0o600
    finally:
        os.umask(previous)


def test_internal_timeout_is_positive_and_below_workflow_limit(runner) -> None:
    assert runner._scan_timeout_seconds({}) == 3300.0
    assert runner._scan_timeout_seconds({"AGRO_GARAK_SCAN_TIMEOUT_SECONDS": "120"}) == 120.0

    with pytest.raises(ValueError, match="AGRO_GARAK_SCAN_TIMEOUT_SECONDS"):
        runner._scan_timeout_seconds({"AGRO_GARAK_SCAN_TIMEOUT_SECONDS": "0"})


def test_blocked_summary_is_sanitized_and_records_adapter_metrics(runner) -> None:
    summary = runner._blocked_summary(
        reason="scan_timeout",
        release_id="candidate-1",
        adapter_metrics={
            "target_success": 39,
            "contract_rejected": 90,
            "error": 0,
        },
    )

    assert summary["approved"] is False
    assert summary["blocking_reasons"] == ["scan_timeout"]
    assert summary["adapter_metrics"]["contract_rejected"] == 90
    assert "prompt" not in json.dumps(summary).lower()


def test_cost_budget_exhaustion_is_always_release_blocking(runner) -> None:
    metrics = runner._empty_adapter_metrics()
    metrics["budget_exhausted"] = 1
    metrics["max_cost_nano_usd"] = 200_000_000

    assert runner._adapter_blocking_reason(metrics, True) == "cost_budget_exhausted"


def test_inflight_cost_reservation_is_release_blocking(runner) -> None:
    metrics = runner._empty_adapter_metrics()
    metrics["reserved_nano_usd"] = 120_000_000
    metrics["max_cost_nano_usd"] = 200_000_000

    assert runner._adapter_blocking_reason(metrics, True) == "adapter_request_inflight"


def test_timeout_writes_blocking_summary_and_closes_adapter(
    runner, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    raw_dir = tmp_path / "raw"
    summary_dir = tmp_path / "summary"
    monkeypatch.setattr(runner, "RAW_DIR", raw_dir)
    monkeypatch.setattr(runner, "SUMMARY_DIR", summary_dir)
    monkeypatch.setattr(runner, "CONFIG_DIR", ROOT / "infra" / "garak")
    monkeypatch.setenv("AGRO_GARAK_RELEASE_ID", "candidate-timeout")
    monkeypatch.setenv("AGRO_GARAK_SCAN_TIMEOUT_SECONDS", "1")
    monkeypatch.setattr(runner, "_wait_adapter", lambda process: None)
    monkeypatch.setattr(
        runner,
        "_adapter_metrics",
        lambda: (
            {
                **runner._empty_adapter_metrics(),
                "success": 7,
                "contract_rejected": 3,
                "total": 10,
                "input_tokens": 1_000,
                "output_tokens": 100,
                "spent_nano_usd": 3_500_000,
                "max_cost_nano_usd": 200_000_000,
            },
            True,
        ),
    )

    class Adapter:
        terminated = False

        def terminate(self) -> None:
            self.terminated = True

        def wait(self, timeout: float) -> int:
            return 0

        def kill(self) -> None:
            raise AssertionError("adapter should terminate cleanly")

    adapter = Adapter()
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *args, **kwargs: adapter)

    def timeout(*args, **kwargs):
        (raw_dir / "candidate-timeout.report.jsonl").write_text(
            '{"entry_type":"attempt"}\n', encoding="utf-8"
        )
        raise subprocess.TimeoutExpired(cmd="garak", timeout=1)

    monkeypatch.setattr(runner.subprocess, "run", timeout)
    previous = os.umask(0o022)
    try:
        assert runner.main() == 1
    finally:
        os.umask(previous)

    summary = json.loads((summary_dir / "candidate-timeout.json").read_text(encoding="utf-8"))
    assert summary["approved"] is False
    assert summary["blocking_reasons"] == ["scan_timeout"]
    assert summary["adapter_metrics"]["total"] == 10
    assert adapter.terminated is True
    assert "prompt" not in json.dumps(summary).lower()
