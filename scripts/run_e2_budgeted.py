"""Run a budget-capped real E2 verifier ablation on reviewed dev cases."""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
from pathlib import Path
from typing import Any

import httpx

from agro_rag.application.query import QueryService
from agro_rag.bootstrap.retrieval import build_retrieval_runtime
from agro_rag.bootstrap.settings import Settings
from agro_rag.evaluation.benchmark import load_benchmark
from agro_rag.infrastructure.corpus import load_catalogue
from agro_rag.infrastructure.openai import OpenAIModel

INPUT_USD_PER_MILLION = 2.50
OUTPUT_USD_PER_MILLION = 10.00
# QueryService performs at most four calls and OpenAIModel caps each output at 768
# tokens. Within the 12k combined-token contract, the worst billable mix is thus
# 8,928 input + 3,072 output tokens.
MAX_QUERY_USD = (8_928 * INPUT_USD_PER_MILLION + 3_072 * OUTPUT_USD_PER_MILLION) / 1_000_000
PAIR_RESERVE_USD = MAX_QUERY_USD * 2


def can_start_pair(*, spent_usd: float, cap_usd: float) -> bool:
    return spent_usd + PAIR_RESERVE_USD <= cap_usd


def _cost(usage: dict[str, Any]) -> float:
    return (
        int(usage["input_tokens"]) * INPUT_USD_PER_MILLION
        + int(usage["output_tokens"]) * OUTPUT_USD_PER_MILLION
    ) / 1_000_000


async def run(args: argparse.Namespace) -> dict[str, Any]:
    config = Settings(catalogue_path=args.catalogue).model_copy(
        update={
            "retrieval_mode": "hybrid",
            "retrieval_tokenizer_model": Settings().embedding_model,
            "retrieval_tokenizer_revision": Settings().embedding_revision,
        }
    )
    if config.openai_api_key is None or not config.openai_model:
        raise ValueError("OpenAI no está configurado")
    catalogue = load_catalogue(args.catalogue)
    benchmark = load_benchmark(args.benchmark, catalogue)
    eligible_cases = tuple(
        case
        for case in benchmark.cases
        if case.split == "dev"
        and case.category == "respondable"
        and case.query_id != args.exclude_query_id
    )
    cases = eligible_cases[args.skip_pairs : args.skip_pairs + args.max_pairs]
    runtime = build_retrieval_runtime(config, catalogue)
    rows: list[dict[str, Any]] = []
    spent = args.prior_cost_usd
    try:
        async with httpx.AsyncClient(trust_env=False) as client:
            model = OpenAIModel(
                client,
                config.openai_url,
                config.openai_api_key.get_secret_value(),
                config.openai_model,
            )
            for case in cases:
                if not can_start_pair(spent_usd=spent, cap_usd=args.cap_usd):
                    break
                pair = []
                for enabled, variant in ((False, "without_verifier"), (True, "with_verifier")):
                    service = QueryService(
                        runtime.retriever,
                        model,
                        catalogue.version,
                        retrieval_mode="hybrid",
                        verifier_enabled=enabled,
                    )
                    result = await service.run(case.question, case.crop, {})
                    cost = _cost(result["usage"])
                    spent += cost
                    pair.append(
                        {
                            "variant": variant,
                            "result": result,
                            "cost_usd": cost,
                        }
                    )
                rows.append(
                    {
                        "query_id": case.query_id,
                        "expected_status": case.expected_status,
                        "pair": pair,
                    }
                )
    finally:
        runtime.close()

    return {
        "experiment_id": "E2-budgeted",
        "execution_kind": "real",
        "split": "dev",
        "commit_sha": subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip(),
        "corpus_version": benchmark.corpus_version,
        "dataset_sha256": benchmark.file_sha256,
        "model": config.openai_model,
        "retrieval_mode": "hybrid",
        "pricing": {
            "as_of": "2026-10-28",
            "input_usd_per_million": INPUT_USD_PER_MILLION,
            "output_usd_per_million": OUTPUT_USD_PER_MILLION,
        },
        "cap_usd": args.cap_usd,
        "prior_cost_usd": args.prior_cost_usd,
        "run_cost_usd": spent - args.prior_cost_usd,
        "total_cost_usd": spent,
        "completed_pairs": len(rows),
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--benchmark", type=Path, default=Path("data/evaluation/benchmark-60.jsonl")
    )
    parser.add_argument("--catalogue", type=Path, default=Path("data/processed/catalogue"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cap-usd", type=float, default=0.50)
    parser.add_argument("--prior-cost-usd", type=float, default=0.0)
    parser.add_argument("--max-pairs", type=int, default=10)
    parser.add_argument("--skip-pairs", type=int, default=0)
    parser.add_argument("--exclude-query-id", default="")
    args = parser.parse_args()
    report = asyncio.run(run(args))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "completed_pairs": report["completed_pairs"],
                "total_cost_usd": round(report["total_cost_usd"], 6),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
