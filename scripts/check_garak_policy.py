"""Evaluate sanitized aggregate garak results against a versioned policy."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

Key = tuple[str, str]


def _object(path: Path | None, default: dict[str, Any]) -> dict[str, Any]:
    if path is None:
        return default
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Formato inválido: {path.name}")
    return value


def _key(value: dict[str, Any]) -> Key:
    return str(value.get("probe", "")), str(value.get("detector", ""))


def _valid_exception(value: dict[str, Any], today: date) -> bool:
    required = ("owner", "risk", "tracking", "expires")
    if any(not isinstance(value.get(field), str) or not value[field].strip() for field in required):
        return False
    try:
        return date.fromisoformat(value["expires"]) >= today
    except ValueError:
        return False


def _valid_triage(value: dict[str, Any]) -> bool:
    if value.get("status") not in {"confirmed", "false_positive"}:
        return False
    if not isinstance(value.get("reviewer"), str) or not value["reviewer"].strip():
        return False
    try:
        date.fromisoformat(value["reviewed_at"])
    except (KeyError, TypeError, ValueError):
        return False
    return True


def evaluate_report(
    report_path: Path,
    policy_path: Path,
    *,
    baseline_path: Path | None = None,
    triage_path: Path | None = None,
    exceptions_path: Path | None = None,
    today: date | None = None,
) -> dict[str, Any]:
    policy = _object(policy_path, {})
    if policy.get("schema_version") != 1 or not isinstance(policy.get("rules"), list):
        raise ValueError("Política Garak inválida")

    evals: dict[Key, dict[str, Any]] = {}
    for line_number, line in enumerate(report_path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSONL Garak inválido en línea {line_number}") from exc
        if isinstance(row, dict) and row.get("entry_type") == "eval":
            key = _key(row)
            if key in evals:
                raise ValueError("Reporte Garak contiene evaluaciones duplicadas")
            evals[key] = row

    baseline_payload = _object(baseline_path, {"schema_version": 1, "results": []})
    triage_payload = _object(triage_path, {"schema_version": 1, "findings": []})
    exception_payload = _object(exceptions_path, {"schema_version": 1, "exceptions": []})
    if any(
        payload.get("schema_version") != 1
        for payload in (baseline_payload, triage_payload, exception_payload)
    ):
        raise ValueError("Artefacto Garak auxiliar inválido")

    baseline_values = baseline_payload.get("results", [])
    baseline = {
        _key(row): float(row["failure_rate"])
        for row in baseline_values
        if isinstance(row, dict) and "failure_rate" in row
    }
    triage_values = triage_payload.get("findings", [])
    triage = {_key(row): row for row in triage_values if isinstance(row, dict)}
    exception_values = exception_payload.get("exceptions", [])
    exceptions = {_key(row): row for row in exception_values if isinstance(row, dict)}

    reasons: set[str] = set()
    results: list[dict[str, Any]] = []
    policy_keys = {_key(rule) for rule in policy["rules"] if isinstance(rule, dict)}
    if set(evals) - policy_keys:
        reasons.add("unruled_eval")
    for rule in policy["rules"]:
        if not isinstance(rule, dict):
            raise ValueError("Regla Garak inválida")
        key = _key(rule)
        severity = str(rule.get("severity", "")).lower()
        if not all(key) or severity not in {"critical", "high", "medium", "low"}:
            raise ValueError("Regla Garak inválida")
        if float(rule.get("max_regression", 0.0)) < 0:
            raise ValueError("Regla Garak inválida")
        row = evals.get(key)
        if row is None:
            reasons.add("missing_eval")
            continue
        passed = int(row.get("passed", 0))
        fails = int(row.get("fails", 0))
        total = int(row.get("total_evaluated", passed + fails))
        failure_rate = fails / total if total else 0.0
        triage_record = triage.get(key, {})
        status = str(triage_record.get("status", "untriaged"))

        if fails and severity in {"critical", "high"}:
            if status == "untriaged":
                reasons.add(f"untriaged_{severity}")
            elif not _valid_triage(triage_record):
                reasons.add("invalid_triage")
            elif status == "confirmed" and not _valid_exception(
                exceptions.get(key, {}), today or date.today()
            ):
                reasons.add(f"confirmed_{severity}")

        if key in baseline:
            tolerance = float(rule.get("max_regression", 0.0))
            if failure_rate > baseline[key] + tolerance:
                reasons.add("regression")

        results.append(
            {
                "probe": key[0],
                "detector": key[1],
                "severity": severity,
                "passed": passed,
                "fails": fails,
                "total_evaluated": total,
                "failure_rate": round(failure_rate, 6),
                "triage_status": status,
                "exception_active": _valid_exception(
                    exceptions.get(key, {}), today or date.today()
                ),
            }
        )

    return {
        "schema_version": 1,
        "approved": not reasons,
        "blocking_reasons": sorted(reasons),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--triage", type=Path)
    parser.add_argument("--exceptions", type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    args = parser.parse_args()
    summary = evaluate_report(
        args.report,
        args.policy,
        baseline_path=args.baseline,
        triage_path=args.triage,
        exceptions_path=args.exceptions,
    )
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {"approved": summary["approved"], "blocking_reasons": summary["blocking_reasons"]}
        )
    )
    return 0 if summary["approved"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
