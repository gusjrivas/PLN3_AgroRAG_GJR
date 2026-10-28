import json
from pathlib import Path

import pytest
from test_retrieval import evidence

from agro_rag.domain.evidence import Catalogue

ROOT = Path(__file__).parents[2]


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


def draft_rows():
    rows = benchmark_rows()
    for row in rows:
        row["annotator"] = "codex-draft"
        row["review_status"] = "pending_human"
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


def test_eva_01_draft_packet_is_balanced_but_cannot_be_promoted_implicitly(tmp_path):
    from agro_rag.evaluation.benchmark import load_benchmark, load_benchmark_draft

    catalogue = Catalogue("v1", (evidence("a", "riego", crop="tomato"),))
    path = write_rows(tmp_path, draft_rows())

    draft = load_benchmark_draft(path, catalogue)

    assert len(draft.cases) == 60
    assert draft.split_counts == {"dev": 30, "test": 30}
    assert draft.category_counts == {
        "respondable": 36,
        "unsupported": 12,
        "adversarial": 12,
    }
    assert draft.pending_human_count == 60
    with pytest.raises(ValueError, match="review"):
        load_benchmark(path, catalogue)


def test_eva_01_draft_packet_rejects_mixed_review_status(tmp_path):
    from agro_rag.evaluation.benchmark import load_benchmark_draft

    rows = draft_rows()
    rows[0]["review_status"] = "reviewed"

    with pytest.raises(ValueError, match="pending_human"):
        load_benchmark_draft(
            write_rows(tmp_path, rows),
            Catalogue("v1", (evidence("a", "riego", crop="tomato"),)),
        )


def test_eva_01_repository_draft_packet_is_complete_and_pending_human():
    from agro_rag.evaluation.benchmark import load_benchmark_draft
    from agro_rag.infrastructure.corpus import load_catalogue

    draft = load_benchmark_draft(
        ROOT / "data/evaluation/benchmark-60-draft.jsonl",
        load_catalogue(ROOT / "data/processed/catalogue"),
    )

    assert draft.split_counts == {"dev": 30, "test": 30}
    assert draft.category_counts == {
        "respondable": 36,
        "unsupported": 12,
        "adversarial": 12,
    }
    assert draft.pending_human_count == 60


def test_cli_validates_draft_packet_without_promoting_it(capsys):
    from agro_rag.bootstrap.cli import main

    result = main(
        [
            "validate-benchmark",
            str(ROOT / "data/evaluation/benchmark-60-draft.jsonl"),
            "--draft",
        ]
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["review_status"] == "pending_human"
    assert payload["case_count"] == 60
    assert payload["pending_human_count"] == 60
