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
from pathlib import Path

from check_garak_policy import evaluate_report

ROOT = Path("/opt/agrorag")
CONFIG_DIR = ROOT / "config"
RAW_DIR = Path("/reports/raw")
SUMMARY_DIR = Path("/reports/summary")


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
    release_id = os.environ.get("AGRO_GARAK_RELEASE_ID", "")
    prefix = _slug(release_id)
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
    try:
        _wait_adapter(adapter)
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
        )
    finally:
        adapter.terminate()
        try:
            adapter.wait(timeout=5)
        except subprocess.TimeoutExpired:
            adapter.kill()
            adapter.wait(timeout=5)

    for raw_file in RAW_DIR.glob(f"{prefix}.*"):
        raw_file.chmod(0o600)
    if completed.returncode != 0:
        return completed.returncode
    if not report_path.is_file():
        raise RuntimeError("Garak no produjo el reporte JSONL esperado")

    summary = evaluate_report(
        report_path,
        CONFIG_DIR / "policy.json",
        baseline_path=CONFIG_DIR / "baseline.json",
        triage_path=CONFIG_DIR / "triage.json",
        exceptions_path=CONFIG_DIR / "exceptions.json",
    )
    summary["release_id"] = release_id
    summary["garak_version"] = "0.17.0"
    summary["config_sha256"] = _sha256(CONFIG_DIR / "garak.yaml")
    summary["policy_sha256"] = _sha256(CONFIG_DIR / "policy.json")
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path.chmod(0o644)
    print(
        json.dumps(
            {
                "approved": summary["approved"],
                "blocking_reasons": summary["blocking_reasons"],
                "summary": str(summary_path),
            }
        )
    )
    return 0 if summary["approved"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
