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


def classify_visible_status(text: str) -> str:
    if "Respuesta verificada automáticamente" in text:
        return "answered"
    if "Falta contexto para responder:" in text:
        return "needs_clarification"
    if "No hay evidencia suficiente para una respuesta verificada." in text:
        return "insufficient_evidence"
    return "unknown"


def make_result(
    case: BenchmarkCase, observed_status: str, elapsed_ms: int, visible_text: str, error: str = ""
) -> dict[str, Any]:
    return {
        "query_id": case.query_id,
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


def run_case(page: Page, case: BenchmarkCase, timeout_ms: int) -> dict[str, Any]:
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
            case, observed, round((time.monotonic() - started) * 1000), visible_text
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
        )


def run_benchmark(
    url: str,
    benchmark_path: Path,
    output_path: Path,
    *,
    limit: int | None,
    headed: bool,
    timeout_seconds: int,
) -> list[dict[str, Any]]:
    cases = load_cases(benchmark_path)
    if limit is not None:
        cases = cases[:limit]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not headed)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        for case in cases:
            result = run_case(page, case, timeout_seconds * 1000)
            results.append(result)
            with output_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(result, ensure_ascii=False) + "\n")
            print(
                f"{case.query_id}: {result['observed_status']} "
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
        headed=args.headed,
        timeout_seconds=args.timeout_seconds,
    )
    if has_runtime_errors(results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
