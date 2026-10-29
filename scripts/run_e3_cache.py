"""Run three real cold and hot retrieval-cache trials under a hard cost cap."""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
from pathlib import Path
from typing import Any, Protocol

import httpx

from agro_rag.application.query import QueryService
from agro_rag.bootstrap.retrieval import build_retrieval_runtime
from agro_rag.bootstrap.settings import Settings
from agro_rag.evaluation.benchmark import load_benchmark
from agro_rag.infrastructure.corpus import load_catalogue
from agro_rag.infrastructure.openai import OpenAIModel

INPUT_USD_PER_MILLION = 2.50
OUTPUT_USD_PER_MILLION = 10.00
OUTPUT_CAP = 256
MAX_RUN_USD = (11_744 * INPUT_USD_PER_MILLION + OUTPUT_CAP * OUTPUT_USD_PER_MILLION) / 1_000_000
RUN_COUNT = 6


class QueryRunner(Protocol):
    async def run(
        self, question: str, crop: str | None, context: dict[str, Any]
    ) -> dict[str, Any]: ...


async def run_cache_trials(
    services: tuple[QueryRunner, QueryRunner, QueryRunner],
    *,
    question: str,
    crop: str | None,
) -> list[dict[str, Any]]:
    rows = []
    for index, service in enumerate(services, 1):
        result = await service.run(question, crop, {})
        if result["usage"]["cache_hit"] is not False:
            raise ValueError("La medición fría informó cache hit")
        rows.append({"variant": "cache_cold", "run_index": index, "result": result})
    for index in range(1, 4):
        result = await services[0].run(question, crop, {})
        if result["usage"]["cache_hit"] is not True:
            raise ValueError("La medición caliente no informó cache hit")
        rows.append({"variant": "cache_hot", "run_index": index, "result": result})
    return rows


def _cost(usage: dict[str, Any]) -> float:
    return (
        int(usage["input_tokens"]) * INPUT_USD_PER_MILLION
        + int(usage["output_tokens"]) * OUTPUT_USD_PER_MILLION
    ) / 1_000_000


async def run(args: argparse.Namespace) -> dict[str, Any]:
    if args.prior_cost_usd + RUN_COUNT * MAX_RUN_USD > args.cap_usd:
        raise ValueError("El peor costo contractual de E3 excede el saldo")
    base = Settings(catalogue_path=args.catalogue)
    config = base.model_copy(
        update={
            "retrieval_mode": "hybrid",
            "retrieval_tokenizer_model": base.embedding_model,
            "retrieval_tokenizer_revision": base.embedding_revision,
        }
    )
    if config.openai_api_key is None or not config.openai_model:
        raise ValueError("OpenAI no está configurado")
    catalogue = load_catalogue(args.catalogue)
    benchmark = load_benchmark(args.benchmark, catalogue)
    case = next(
        case
        for case in benchmark.cases
        if case.query_id == args.query_id and case.split == "dev" and case.category == "respondable"
    )
    runtime = build_retrieval_runtime(config, catalogue)
    try:
        async with httpx.AsyncClient(trust_env=False) as client:
            model = OpenAIModel(
                client,
                config.openai_url,
                config.openai_api_key.get_secret_value(),
                config.openai_model,
                max_output_tokens=OUTPUT_CAP,
            )
            services = tuple(
                QueryService(
                    runtime.retriever,
                    model,
                    catalogue.version,
                    retrieval_mode="hybrid",
                    verifier_enabled=False,
                )
                for _ in range(3)
            )
            rows = await run_cache_trials(services, question=case.question, crop=case.crop)  # type: ignore[arg-type]
    finally:
        runtime.close()
    run_cost = sum(_cost(row["result"]["usage"]) for row in rows)
    return {
        "experiment_id": "E3-budgeted",
        "execution_kind": "real",
        "query_id": case.query_id,
        "split": "dev",
        "commit_sha": subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip(),
        "corpus_version": benchmark.corpus_version,
        "dataset_sha256": benchmark.file_sha256,
        "model": config.openai_model,
        "retrieval_mode": "hybrid",
        "verifier_enabled": False,
        "max_output_tokens": OUTPUT_CAP,
        "cap_usd": args.cap_usd,
        "prior_cost_usd": args.prior_cost_usd,
        "run_cost_usd": run_cost,
        "total_cost_usd": args.prior_cost_usd + run_cost,
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--benchmark", type=Path, default=Path("data/evaluation/benchmark-60.jsonl")
    )
    parser.add_argument("--catalogue", type=Path, default=Path("data/processed/catalogue"))
    parser.add_argument("--query-id", default="dev-r-001")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cap-usd", type=float, default=0.50)
    parser.add_argument("--prior-cost-usd", type=float, required=True)
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
                "run_cost_usd": round(report["run_cost_usd"], 6),
                "total_cost_usd": round(report["total_cost_usd"], 6),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
