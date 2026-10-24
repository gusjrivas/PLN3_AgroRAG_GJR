import json

import pytest
from test_retrieval import evidence

from agro_rag.domain.evidence import Catalogue


def benchmark_rows():
    rows = []
    for split in ("dev", "test"):
        for category, count, status in (
            ("respondable", 18, "answered"),
            ("unsupported", 6, "insufficient_evidence"),
            ("adversarial", 6, "needs_clarification"),
        ):
            for index in range(count):
                rows.append(
                    {
                        "query_id": f"{split}-{category}-{index}",
                        "family_id": f"{split}-{category}-{index}",
                        "question": f"pregunta {split} {category} {index}",
                        "crop": "tomato",
                        "category": category,
                        "expected_status": status,
                        "reference_answer": "respuesta" if category == "respondable" else "",
                        "required_claims": ["claim"] if category == "respondable" else [],
                        "relevant_evidence_ids": ["a"] if category == "respondable" else [],
                        "source_pages": ["S:1"] if category == "respondable" else [],
                        "split": split,
                        "annotator": "human-1",
                        "review_status": "reviewed",
                        "corpus_version": "v1",
                    }
                )
    return rows


def write_rows(tmp_path, rows):
    path = tmp_path / "benchmark.jsonl"
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def test_eva_01_split_and_denominators_are_frozen(tmp_path):
    from agro_rag.evaluation.benchmark import load_benchmark

    dataset = load_benchmark(
        write_rows(tmp_path, benchmark_rows()),
        Catalogue("v1", (evidence("a", "riego", crop="tomato"),)),
    )

    assert len(dataset.cases) == 60
    assert dataset.split_counts == {"dev": 30, "test": 30}
    assert dataset.category_counts == {
        "respondable": 36,
        "unsupported": 12,
        "adversarial": 12,
    }
    assert len(dataset.ir_cases) == 36
    assert len(dataset.abstention_cases) == 24
    assert len(dataset.file_sha256) == 64


def test_eva_01_rejects_family_leakage_and_unknown_evidence(tmp_path):
    from agro_rag.evaluation.benchmark import load_benchmark

    catalogue = Catalogue("v1", (evidence("a", "riego", crop="tomato"),))
    rows = benchmark_rows()
    rows[30]["family_id"] = rows[0]["family_id"]
    with pytest.raises(ValueError, match="familia"):
        load_benchmark(write_rows(tmp_path, rows), catalogue)

    rows = benchmark_rows()
    rows[0]["relevant_evidence_ids"] = ["missing"]
    with pytest.raises(ValueError, match="evidencia"):
        load_benchmark(write_rows(tmp_path, rows), catalogue)


def test_eva_01_unanswerable_cases_never_enter_ir_denominator(tmp_path):
    from agro_rag.evaluation.benchmark import load_benchmark

    catalogue = Catalogue("v1", (evidence("a", "riego", crop="tomato"),))
    rows = benchmark_rows()
    rows[18]["relevant_evidence_ids"] = ["a"]

    with pytest.raises(ValueError, match="sin soporte"):
        load_benchmark(write_rows(tmp_path, rows), catalogue)
