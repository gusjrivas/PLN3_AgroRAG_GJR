from pathlib import Path

import pdfplumber

from scripts.build_benchmark_checklist import build_checklist

ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = ROOT / "data" / "evaluation" / "benchmark-60-draft.jsonl"


def test_fillable_checklist_has_pass_fail_and_notes_for_every_case(tmp_path: Path) -> None:
    output = tmp_path / "benchmark-checklist.pdf"

    build_checklist(BENCHMARK, output)

    raw_pdf = output.read_bytes()
    assert raw_pdf.count(b"/T (pass_") == 60
    assert raw_pdf.count(b"/T (fail_") == 60
    assert raw_pdf.count(b"/T (observed_") == 60
    assert raw_pdf.count(b"/T (notes_") == 60
    with pdfplumber.open(output) as pdf:
        assert len(pdf.pages) >= 31
