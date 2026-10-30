"""Run the real E1 retrieval ablation on the frozen human-reviewed benchmark."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Literal, cast

from agro_rag.application.retrieval_pipeline import CandidateRanker
from agro_rag.bootstrap.retrieval import build_retrieval_runtime
from agro_rag.bootstrap.settings import Settings
from agro_rag.evaluation.benchmark import BenchmarkDataset, load_benchmark
from agro_rag.evaluation.retrieval import RetrievalCase, RetrievalDataset, run_benchmark
from agro_rag.infrastructure.corpus import load_catalogue

Split = Literal["dev", "test"]
MODES = ("bm25", "vector", "hybrid", "hybrid_rerank")


def select_ir_cases(benchmark: BenchmarkDataset, *, split: Split) -> RetrievalDataset:
    """Adapt the reviewed respondable partition without changing its frozen identity."""
    selected = tuple(
        RetrievalCase(
            query_id=case.query_id,
            question=case.question,
            crop=case.crop,
            relevant_evidence_ids=case.relevant_evidence_ids,
            corpus_version=case.corpus_version,
            annotator=case.annotator,
            review_status="reviewed",
        )
        for case in benchmark.cases
        if case.split == split and case.category == "respondable"
    )
    if not selected:
        raise ValueError(f"El split {split} no contiene casos IR")
    return RetrievalDataset(
        corpus_version=benchmark.corpus_version,
        file_sha256=benchmark.file_sha256,
        cases=selected,
    )


def _commit_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--benchmark", type=Path, default=Path("data/evaluation/benchmark-60.jsonl")
    )
    parser.add_argument("--catalogue", type=Path, default=Path("data/processed/catalogue"))
    parser.add_argument("--split", choices=("dev", "test"), default="dev")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    base = Settings(catalogue_path=args.catalogue)
    catalogue = load_catalogue(args.catalogue)
    benchmark = load_benchmark(args.benchmark, catalogue)
    dataset = select_ir_cases(benchmark, split=args.split)
    runs = []
    for mode in MODES:
        config = base.model_copy(
            update={
                "retrieval_mode": mode,
                # E1 holds one local tokenizer fixed across all variants. This is an
                # evidence-selection budget, not OpenAI generation accounting.
                "retrieval_tokenizer_model": base.embedding_model,
                "retrieval_tokenizer_revision": base.embedding_revision,
            }
        )
        runtime = build_retrieval_runtime(config, catalogue)
        try:
            ranker = cast(CandidateRanker, runtime.retriever)
            runs.append(asdict(run_benchmark(mode=mode, ranker=ranker, dataset=dataset)))
        finally:
            runtime.close()

    payload = {
        "experiment_id": "E1",
        "execution_kind": "real",
        "split": args.split,
        "commit_sha": _commit_sha(),
        "corpus_version": benchmark.corpus_version,
        "dataset_sha256": benchmark.file_sha256,
        "human_reviewed": dataset.is_human_reviewed,
        "query_count": len(dataset.cases),
        "embedding_model": base.embedding_model,
        "embedding_revision": base.embedding_revision,
        "reranker_model": base.reranker_model,
        "reranker_revision": base.reranker_revision,
        "tokenizer_model": base.embedding_model,
        "tokenizer_revision": base.embedding_revision,
        "runs": runs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(args.output), "query_count": len(dataset.cases)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
