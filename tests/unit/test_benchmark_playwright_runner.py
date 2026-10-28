import json
from pathlib import Path

from scripts.run_benchmark_playwright import (
    BenchmarkCase,
    classify_visible_status,
    has_runtime_errors,
    load_cases,
    make_result,
)


def test_load_cases_preserves_the_60_case_contract(tmp_path: Path) -> None:
    benchmark = tmp_path / "benchmark.jsonl"
    rows = [
        {
            "query_id": f"case-{index:02d}",
            "question": f"Pregunta {index}",
            "crop": "lettuce",
            "expected_status": "answered",
        }
        for index in range(60)
    ]
    benchmark.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8"
    )

    cases = load_cases(benchmark)

    assert len(cases) == 60
    assert cases[0].query_id == "case-00"
    assert cases[-1].question == "Pregunta 59"


def test_classify_visible_status_uses_the_ui_contract() -> None:
    assert classify_visible_status("Respuesta verificada automáticamente") == "answered"
    assert classify_visible_status("Falta contexto para responder:") == "needs_clarification"
    assert (
        classify_visible_status("No hay evidencia suficiente para una respuesta verificada.")
        == "insufficient_evidence"
    )
    assert classify_visible_status("Streamlit se está iniciando") == "unknown"


def test_result_passes_only_when_observed_status_matches() -> None:
    case = BenchmarkCase(
        query_id="dev-r-001",
        question="¿Qué temperatura favorece a la lechuga?",
        crop="lettuce",
        expected_status="answered",
    )

    result = make_result(case, "answered", 1234, "Respuesta visible")

    assert result["status_pass"] is True
    assert result["elapsed_ms"] == 1234
    assert result["observed_status"] == "answered"


def test_runtime_error_makes_the_run_unsuccessful() -> None:
    assert has_runtime_errors([{"observed_status": "error"}]) is True
    assert has_runtime_errors([{"observed_status": "answered"}]) is False
