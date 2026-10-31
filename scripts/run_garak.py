"""Run the local adapter, pinned garak scan and aggregate release gate."""

from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.request import urlopen

from check_garak_policy import evaluate_report

ROOT = Path("/opt/agrorag")
CONFIG_DIR = ROOT / "config"
RAW_DIR = Path("/reports/raw")
SUMMARY_DIR = Path("/reports/summary")
ADAPTER_METRICS_URL = "http://127.0.0.1:8090/metrics"
ADAPTER_METRIC_NAMES = (
    "success",
    "contract_rejected",
    "budget_exhausted",
    "error",
    "total",
    "input_tokens",
    "output_tokens",
    "spent_nano_usd",
    "reserved_nano_usd",
    "max_cost_nano_usd",
)


def _empty_adapter_metrics() -> dict[str, int]:
    return dict.fromkeys(ADAPTER_METRIC_NAMES, 0)


def _set_private_umask() -> None:
    os.umask(0o077)


def _scan_timeout_seconds(environment: Mapping[str, str]) -> float:
    name = "AGRO_GARAK_SCAN_TIMEOUT_SECONDS"
    try:
        value = float(environment.get(name, "3300"))
    except ValueError as exc:
        raise ValueError(f"{name} debe ser numérico") from exc
    if value <= 0 or value >= 3600:
        raise ValueError(f"{name} debe ser mayor que 0 y menor que 3600")
    return value


def _blocked_summary(
    *,
    reason: str,
    release_id: str,
    adapter_metrics: dict[str, int],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "approved": False,
        "blocking_reasons": [reason],
        "release_id": release_id,
        "garak_version": "0.17.0",
        "adapter_metrics": adapter_metrics,
        "results": [],
    }


def _adapter_metrics() -> tuple[dict[str, int], bool]:
    try:
        with urlopen(ADAPTER_METRICS_URL, timeout=2) as response:  # noqa: S310
            body = json.load(response)
        if not isinstance(body, dict) or any(
            not isinstance(body.get(name), int) or body[name] < 0 for name in ADAPTER_METRIC_NAMES
        ):
            raise ValueError("invalid adapter metrics")
        metrics = {name: body[name] for name in ADAPTER_METRIC_NAMES}
        if metrics["spent_nano_usd"] + metrics["reserved_nano_usd"] > metrics["max_cost_nano_usd"]:
            raise ValueError("invalid adapter cost metrics")
        return metrics, True
    except (OSError, TimeoutError, ValueError, json.JSONDecodeError):
        return _empty_adapter_metrics(), False


def _adapter_blocking_reason(metrics: Mapping[str, int], available: bool) -> str | None:
    if not available:
        return "adapter_metrics_unavailable"
    if metrics["budget_exhausted"]:
        return "cost_budget_exhausted"
    if metrics["error"]:
        return "adapter_error"
    if metrics["reserved_nano_usd"]:
        return "adapter_request_inflight"
    return None


def _write_summary(path: Path, summary: dict[str, Any]) -> None:
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(0o644)


def _add_release_metadata(summary: dict[str, Any]) -> None:
    summary["config_sha256"] = _sha256(CONFIG_DIR / "garak.yaml")
    summary["policy_sha256"] = _sha256(CONFIG_DIR / "policy.json")


def _print_decision(summary_path: Path, summary: dict[str, Any]) -> None:
    print(
        json.dumps(
            {
                "approved": summary["approved"],
                "blocking_reasons": summary["blocking_reasons"],
                "summary": str(summary_path),
            }
        )
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _slug(value: str) -> str:
    result = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-.")
    if not result:
        raise ValueError("AGRO_GARAK_RELEASE_ID inválido")
    return result[:80]


def _wait_adapter(process: subprocess.Popen[bytes], timeout: float = 15.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("El adaptador Garak no pudo iniciar")
        try:
            with socket.create_connection(("127.0.0.1", 8090), timeout=0.5):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("Timeout iniciando el adaptador Garak")


def main() -> int:
    _set_private_umask()
    release_id = os.environ.get("AGRO_GARAK_RELEASE_ID", "")
    prefix = _slug(release_id)
    scan_timeout = _scan_timeout_seconds(os.environ)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    report_path = RAW_DIR / f"{prefix}.report.jsonl"
    summary_path = SUMMARY_DIR / f"{prefix}.json"
    if report_path.exists() or summary_path.exists():
        raise RuntimeError("Ya existe evidencia para esta release; use un directorio limpio")

    adapter = subprocess.Popen(
        [sys.executable, str(ROOT / "garak_adapter.py")],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    completed: subprocess.CompletedProcess[bytes] | None = None
    timed_out = False
    metrics = _empty_adapter_metrics()
    metrics_available = False
    try:
        _wait_adapter(adapter)
        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "garak",
                    "--config",
                    str(CONFIG_DIR / "garak.yaml"),
                    "--report_prefix",
                    prefix,
                ],
                check=False,
                timeout=scan_timeout,
            )
        except subprocess.TimeoutExpired:
            timed_out = True
        metrics, metrics_available = _adapter_metrics()
    finally:
        adapter.terminate()
        try:
            adapter.wait(timeout=5)
        except subprocess.TimeoutExpired:
            adapter.kill()
            adapter.wait(timeout=5)

    for raw_file in RAW_DIR.glob(f"{prefix}.*"):
        raw_file.chmod(0o600)

    blocked_reason: str | None = None
    if timed_out:
        blocked_reason = "scan_timeout"
    elif completed is None or completed.returncode != 0:
        blocked_reason = "garak_exit_nonzero"
    elif not report_path.is_file():
        blocked_reason = "report_missing"
    else:
        blocked_reason = _adapter_blocking_reason(metrics, metrics_available)

    if blocked_reason is not None:
        summary = _blocked_summary(
            reason=blocked_reason,
            release_id=release_id,
            adapter_metrics=metrics,
        )
        _add_release_metadata(summary)
        _write_summary(summary_path, summary)
        _print_decision(summary_path, summary)
        return 1

    summary = evaluate_report(
        report_path,
        CONFIG_DIR / "policy.json",
        baseline_path=CONFIG_DIR / "baseline.json",
        triage_path=CONFIG_DIR / "triage.json",
        exceptions_path=CONFIG_DIR / "exceptions.json",
    )
    summary["release_id"] = release_id
    summary["garak_version"] = "0.17.0"
    summary["adapter_metrics"] = metrics
    _add_release_metadata(summary)
    _write_summary(summary_path, summary)
    _print_decision(summary_path, summary)
    return 0 if summary["approved"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
