import hashlib
import json
import math
from pathlib import Path

import pytest
from test_retrieval import evidence

from agro_rag.domain.evidence import Catalogue


def test_frozen_dev_dataset_has_expected_bytes() -> None:
    content = Path("data/evaluation/retrieval-dev-draft.jsonl").read_bytes()

    assert hashlib.sha256(content).hexdigest() == (
        "bfe832f33b8683f0680953bba2b215c3e981b05867c30f29a8a7f30d1807d34f"
    )


def test_retrieval_metrics_match_binary_qrels_at_each_cutoff() -> None:
    from agro_rag.evaluation.retrieval import evaluate_ranking

    result = evaluate_ranking(
        query_id="q-1",
        predicted_ids=("a", "b", "c", "d"),
        relevant_ids=frozenset({"a", "c"}),
        cutoffs=(1, 3),
    )

    assert result.query_id == "q-1"
    assert result.relevant_count == 2
    assert result.retrieved_count == 4
    assert result.reciprocal_rank == 1.0
    assert result.at_cutoff[0].precision == 1.0
    assert result.at_cutoff[0].recall == 0.5
    assert result.at_cutoff[0].hit == 1.0
    assert result.at_cutoff[0].ndcg == 1.0
    assert result.at_cutoff[1].precision == pytest.approx(2 / 3)
    assert result.at_cutoff[1].recall == 1.0
    expected_dcg = 1.0 + 1.0 / math.log2(4)
    expected_idcg = 1.0 + 1.0 / math.log2(3)
    assert result.at_cutoff[1].ndcg == pytest.approx(expected_dcg / expected_idcg)


def test_retrieval_metrics_reject_invalid_or_duplicate_rankings() -> None:
    from agro_rag.evaluation.retrieval import evaluate_ranking

    with pytest.raises(ValueError, match="relevante"):
        evaluate_ranking("q", ("a",), frozenset(), (1,))
    with pytest.raises(ValueError, match="duplicados"):
        evaluate_ranking("q", ("a", "a"), frozenset({"a"}), (1,))
    with pytest.raises(ValueError, match="cutoffs"):
        evaluate_ranking("q", ("a",), frozenset({"a"}), (0,))


def test_macro_summary_preserves_denominators_and_cutoffs() -> None:
    from agro_rag.evaluation.retrieval import evaluate_ranking, summarize

    rows = (
        evaluate_ranking("q-1", ("a", "x"), frozenset({"a"}), (1, 2)),
        evaluate_ranking("q-2", ("x", "b"), frozenset({"b"}), (1, 2)),
    )

    summary = summarize(rows)

    assert summary.query_count == 2
    assert summary.mean_reciprocal_rank == 0.75
    assert summary.at_cutoff[0].k == 1
    assert summary.at_cutoff[0].precision == 0.5
    assert summary.at_cutoff[0].recall == 0.5
    assert summary.at_cutoff[0].hit == 0.5
    assert summary.at_cutoff[1].k == 2
    assert summary.at_cutoff[1].precision == 0.5
    assert summary.at_cutoff[1].recall == 1.0
    assert summary.at_cutoff[1].hit == 1.0


def test_load_cases_binds_qrels_to_catalogue_and_hashes_exact_file(tmp_path) -> None:
    from agro_rag.evaluation.retrieval import load_cases

    rows = [
        {
            "query_id": "q-1",
            "question": "¿Cuándo necesita agua el tomate?",
            "crop": "tomato",
            "relevant_evidence_ids": ["a"],
            "corpus_version": "v1",
            "annotator": "codex-draft",
            "review_status": "pending_human",
        },
        {
            "query_id": "q-2",
            "question": "¿Qué es la evapotranspiración?",
            "crop": None,
            "relevant_evidence_ids": ["b"],
            "corpus_version": "v1",
            "annotator": "codex-draft",
            "review_status": "pending_human",
        },
    ]
    content = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    path = tmp_path / "cases.jsonl"
    path.write_text(content, encoding="utf-8")
    catalogue = Catalogue(
        "v1",
        (evidence("a", "tomate", crop="tomato"), evidence("b", "evapotranspiración")),
    )

    dataset = load_cases(path, catalogue)

    assert dataset.corpus_version == "v1"
    assert dataset.file_sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert dataset.is_human_reviewed is False
    assert [case.query_id for case in dataset.cases] == ["q-1", "q-2"]
    assert dataset.cases[0].relevant_evidence_ids == frozenset({"a"})


@pytest.mark.parametrize(
    "change,match",
    [
        ({"corpus_version": "other"}, "corpus"),
        ({"relevant_evidence_ids": ["missing"]}, "catálogo"),
        ({"unexpected": True}, "campos"),
    ],
)
def test_load_cases_rejects_untraceable_qrels(tmp_path, change, match) -> None:
    from agro_rag.evaluation.retrieval import load_cases

    row = {
        "query_id": "q-1",
        "question": "pregunta",
        "crop": "tomato",
        "relevant_evidence_ids": ["a"],
        "corpus_version": "v1",
        "annotator": "codex-draft",
        "review_status": "pending_human",
    }
    row.update(change)
    path = tmp_path / "cases.jsonl"
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    catalogue = Catalogue("v1", (evidence("a", "tomate", crop="tomato"),))

    with pytest.raises(ValueError, match=match):
        load_cases(path, catalogue)


def test_run_benchmark_records_rankings_latency_and_macro_metrics() -> None:
    from agro_rag.application.retrieval_pipeline import ScoredId
    from agro_rag.evaluation.retrieval import (
        RetrievalCase,
        RetrievalDataset,
        run_benchmark,
    )

    class Ranker:
        corpus_version = "v1"

        def rank(self, question, crop):
            if question == "uno":
                return (ScoredId("a", 2.0), ScoredId("x", 1.0))
            return (ScoredId("x", 2.0), ScoredId("b", 1.0))

    times = iter((10.0, 10.01, 20.0, 20.02))
    dataset = RetrievalDataset(
        corpus_version="v1",
        file_sha256="f" * 64,
        cases=(
            RetrievalCase("q-1", "uno", None, frozenset({"a"}), "v1", "human", "reviewed"),
            RetrievalCase("q-2", "dos", "tomato", frozenset({"b"}), "v1", "human", "reviewed"),
        ),
    )

    run = run_benchmark(
        mode="bm25",
        ranker=Ranker(),
        dataset=dataset,
        cutoffs=(1, 2),
        clock=lambda: next(times),
    )

    assert run.mode == "bm25"
    assert run.dataset_sha256 == "f" * 64
    assert run.query_count == 2
    assert run.queries[0].predicted_ids == ("a", "x")
    assert run.queries[0].latency_ms == pytest.approx(10.0)
    assert run.queries[1].latency_ms == pytest.approx(20.0)
    assert run.summary.mean_reciprocal_rank == 0.75
    assert run.summary.at_cutoff[1].recall == 1.0
    assert run.latency.mean_ms == pytest.approx(15.0)
    assert run.latency.p50_ms == pytest.approx(15.0)
    assert run.latency.p95_ms == pytest.approx(19.5)
