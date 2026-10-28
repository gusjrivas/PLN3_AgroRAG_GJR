"""Run the 60-case live benchmark through the Streamlit UI with Playwright."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright


@dataclass(frozen=True)
class BenchmarkCase:
    query_id: str
    question: str
    crop: str | None
    expected_status: str


def load_cases(path: Path) -> list[BenchmarkCase]:
    return [
        BenchmarkCase(
            query_id=row["query_id"],
            question=row["question"],
            crop=row.get("crop"),
            expected_status=row["expected_status"],
        )
        for line in path.read_text(encoding="utf-8").splitlines()
        if line and (row := json.loads(line))
    ]


def select_cases(
    cases: list[BenchmarkCase], query_ids: list[str] | None, limit: int | None
) -> list[BenchmarkCase]:
    selected = cases
    if query_ids:
        requested = set(query_ids)
        known = {case.query_id for case in cases}
        missing = requested - known
        if missing:
            raise ValueError(f"Unknown query ids: {', '.join(sorted(missing))}")
        selected = [case for case in cases if case.query_id in requested]
    return selected if limit is None else selected[:limit]


def classify_visible_status(text: str) -> str:
    if "Respuesta verificada automáticamente" in text:
        return "answered"
    if "Falta contexto para responder:" in text:
        return "needs_clarification"
    if "No hay evidencia suficiente para una respuesta verificada." in text:
        return "insufficient_evidence"
    return "unknown"


def make_result(
    case: BenchmarkCase,
    observed_status: str,
    elapsed_ms: int,
    visible_text: str,
    error: str = "",
    *,
    run_index: int = 1,
) -> dict[str, Any]:
    return {
        "query_id": case.query_id,
        "run_index": run_index,
        "question": case.question,
        "crop": case.crop,
        "expected_status": case.expected_status,
        "observed_status": observed_status,
        "status_pass": observed_status == case.expected_status,
        "elapsed_ms": elapsed_ms,
        "visible_text": visible_text[:4000],
        "error": error,
    }


def has_runtime_errors(results: list[dict[str, Any]]) -> bool:
    return any(result.get("observed_status") == "error" for result in results)


def summarize_stability(results: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        grouped.setdefault(str(result["query_id"]), []).append(result)
    summary = {}
    for query_id, rows in grouped.items():
        counts: dict[str, int] = {}
        for row in rows:
            status = str(row["observed_status"])
            counts[status] = counts.get(status, 0) + 1
        summary[query_id] = {
            "runs": len(rows),
            "status_counts": counts,
            "stable": len(counts) == 1 and "error" not in counts,
            "pass_rate": sum(bool(row["status_pass"]) for row in rows) / len(rows),
        }
    return summary


def run_case(
    page: Page, case: BenchmarkCase, timeout_ms: int, *, run_index: int = 1
) -> dict[str, Any]:
    started = time.monotonic()
    try:
        page.get_by_text("Respuesta verificada", exact=True).click()
        page.locator("textarea").first.fill(case.question)
        crop_label = {"tomato": "Tomate", "lettuce": "Lechuga"}.get(case.crop, "Sin especificar")
        page.get_by_role("combobox", name="Cultivo").click()
        page.get_by_role("option", name=crop_label, exact=True).click()
        page.get_by_role("button", name="Consultar", exact=True).click()
        page.get_by_role("button", name="Nueva consulta").wait_for(timeout=timeout_ms)
        visible_text = page.locator("body").inner_text()
        observed = classify_visible_status(visible_text)
        result = make_result(
            case,
            observed,
            round((time.monotonic() - started) * 1000),
            visible_text,
            run_index=run_index,
        )
        page.get_by_role("button", name="Nueva consulta").click()
        page.get_by_role("button", name="Consultar", exact=True).wait_for(timeout=timeout_ms)
        return result
    except Exception as exc:  # Playwright failures must be persisted per case.
        return make_result(
            case,
            "error",
            round((time.monotonic() - started) * 1000),
            page.locator("body").inner_text() if page.locator("body").count() else "",
            f"{type(exc).__name__}: {exc}",
            run_index=run_index,
        )


def run_benchmark(
    url: str,
    benchmark_path: Path,
    output_path: Path,
    *,
    limit: int | None,
    query_ids: list[str] | None,
    repeat: int,
    headed: bool,
    timeout_seconds: int,
) -> list[dict[str, Any]]:
    cases = select_cases(load_cases(benchmark_path), query_ids, limit)
    if repeat <= 0:
        raise ValueError("repeat must be positive")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not headed)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        for run_index in range(1, repeat + 1):
            for case in cases:
                result = run_case(page, case, timeout_seconds * 1000, run_index=run_index)
                results.append(result)
                with output_path.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(result, ensure_ascii=False) + "\n")
                print(
                    f"run {run_index}/{repeat} {case.query_id}: "
                    f"{result['observed_status']} "
                    f"({'PASS' if result['status_pass'] else 'FAIL'})"
                )
                if result["observed_status"] == "error":
                    page.goto(url, wait_until="domcontentloaded")
        browser.close()
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8501")
    parser.add_argument(
        "--benchmark", type=Path, default=Path("data/evaluation/benchmark-60-draft.jsonl")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("output/evaluation/benchmark-live-results.jsonl")
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument("--query-id", action="append", dest="query_ids")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=90)
    args = parser.parse_args()
    if args.output.exists():
        args.output.unlink()
    results = run_benchmark(
        args.url,
        args.benchmark,
        args.output,
        limit=args.limit,
        query_ids=args.query_ids,
        repeat=args.repeat,
        headed=args.headed,
        timeout_seconds=args.timeout_seconds,
    )
    summary_path = args.output.with_suffix(".summary.json")
    summary_path.write_text(
        json.dumps(summarize_stability(results), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if has_runtime_errors(results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
