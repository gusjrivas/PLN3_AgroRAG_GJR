"""Deterministic binary-qrels metrics adapted from the Teoria1 RAG example."""

from __future__ import annotations

import hashlib
import json
import math
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from agro_rag.application.retrieval_pipeline import CandidateRanker
from agro_rag.domain.evidence import Catalogue

Crop = Literal["tomato", "lettuce"]
ReviewStatus = Literal["pending_human", "reviewed"]


@dataclass(frozen=True)
class CutoffMetrics:
    k: int
    precision: float
    recall: float
    ndcg: float
    hit: float


@dataclass(frozen=True)
class RetrievalMetrics:
    query_id: str
    relevant_count: int
    retrieved_count: int
    reciprocal_rank: float
    at_cutoff: tuple[CutoffMetrics, ...]


@dataclass(frozen=True)
class AggregateMetrics:
    query_count: int
    mean_reciprocal_rank: float
    at_cutoff: tuple[CutoffMetrics, ...]


@dataclass(frozen=True)
class RetrievalCase:
    query_id: str
    question: str
    crop: Crop | None
    relevant_evidence_ids: frozenset[str]
    corpus_version: str
    annotator: str
    review_status: ReviewStatus


@dataclass(frozen=True)
class RetrievalDataset:
    corpus_version: str
    file_sha256: str
    cases: tuple[RetrievalCase, ...]

    @property
    def is_human_reviewed(self) -> bool:
        return all(case.review_status == "reviewed" for case in self.cases)


@dataclass(frozen=True)
class QueryBenchmark:
    metrics: RetrievalMetrics
    predicted_ids: tuple[str, ...]
    latency_ms: float


@dataclass(frozen=True)
class LatencyMetrics:
    mean_ms: float
    p50_ms: float
    p95_ms: float


@dataclass(frozen=True)
class BenchmarkRun:
    mode: str
    corpus_version: str
    dataset_sha256: str
    queries: tuple[QueryBenchmark, ...]
    summary: AggregateMetrics
    latency: LatencyMetrics

    @property
    def query_count(self) -> int:
        return len(self.queries)


_CASE_FIELDS = {
    "query_id",
    "question",
    "crop",
    "relevant_evidence_ids",
    "corpus_version",
    "annotator",
    "review_status",
}


def _case_from_json(value: object, catalogue: Catalogue) -> RetrievalCase:
    if not isinstance(value, Mapping) or set(value) != _CASE_FIELDS:
        raise ValueError("Caso con campos inválidos")
    query_id = value["query_id"]
    question = value["question"]
    crop = value["crop"]
    relevant = value["relevant_evidence_ids"]
    corpus_version = value["corpus_version"]
    annotator = value["annotator"]
    review_status = value["review_status"]
    if (
        not isinstance(query_id, str)
        or not query_id
        or not isinstance(question, str)
        or not question.strip()
        or crop not in (None, "tomato", "lettuce")
        or not isinstance(corpus_version, str)
        or corpus_version != catalogue.version
        or not isinstance(annotator, str)
        or not annotator
        or review_status not in ("pending_human", "reviewed")
    ):
        raise ValueError("Caso inválido o de otro corpus")
    if (
        not isinstance(relevant, list)
        or not relevant
        or any(not isinstance(item_id, str) or not item_id for item_id in relevant)
        or len(relevant) != len(set(relevant))
    ):
        raise ValueError("IDs relevantes inválidos")
    items = {item.evidence_id: item for item in catalogue.evidence}
    if any(item_id not in items for item_id in relevant):
        raise ValueError("Qrels no resolubles en el catálogo")
    if crop and any(items[item_id].crop not in (None, crop) for item_id in relevant):
        raise ValueError("Qrels incompatibles con el cultivo")
    return RetrievalCase(
        query_id=query_id,
        question=question,
        crop=crop,
        relevant_evidence_ids=frozenset(relevant),
        corpus_version=corpus_version,
        annotator=annotator,
        review_status=review_status,
    )


def load_cases(path: Path, catalogue: Catalogue) -> RetrievalDataset:
    raw = path.read_bytes()
    try:
        values = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("JSONL de evaluación inválido") from exc
    cases = tuple(_case_from_json(value, catalogue) for value in values)
    if not cases or len({case.query_id for case in cases}) != len(cases):
        raise ValueError("Dataset vacío o con query_id duplicado")
    return RetrievalDataset(
        corpus_version=catalogue.version,
        file_sha256=hashlib.sha256(raw).hexdigest(),
        cases=cases,
    )


def _validate(
    query_id: str,
    predicted_ids: tuple[str, ...],
    relevant_ids: frozenset[str],
    cutoffs: tuple[int, ...],
) -> None:
    if not query_id or any(not item_id for item_id in (*predicted_ids, *relevant_ids)):
        raise ValueError("IDs de evaluación inválidos")
    if not relevant_ids:
        raise ValueError("La consulta debe tener al menos un ID relevante")
    if len(predicted_ids) != len(set(predicted_ids)):
        raise ValueError("El ranking contiene IDs duplicados")
    if not cutoffs or any(k <= 0 for k in cutoffs) or tuple(sorted(set(cutoffs))) != cutoffs:
        raise ValueError("Los cutoffs deben ser positivos, únicos y crecientes")


def evaluate_ranking(
    query_id: str,
    predicted_ids: tuple[str, ...],
    relevant_ids: frozenset[str],
    cutoffs: tuple[int, ...] = (5, 10, 20),
) -> RetrievalMetrics:
    """Evaluate one respondible query; unsupported queries use status metrics elsewhere."""
    _validate(query_id, predicted_ids, relevant_ids, cutoffs)
    maximum = cutoffs[-1]
    reciprocal_rank = 0.0
    for rank, item_id in enumerate(predicted_ids[:maximum], 1):
        if item_id in relevant_ids:
            reciprocal_rank = 1.0 / rank
            break

    rows = []
    for k in cutoffs:
        top = predicted_ids[:k]
        relevant_retrieved = sum(item_id in relevant_ids for item_id in top)
        dcg = math.fsum(
            1.0 / math.log2(rank + 2) for rank, item_id in enumerate(top) if item_id in relevant_ids
        )
        ideal_count = min(k, len(relevant_ids))
        idcg = math.fsum(1.0 / math.log2(rank + 2) for rank in range(ideal_count))
        rows.append(
            CutoffMetrics(
                k=k,
                precision=relevant_retrieved / k,
                recall=relevant_retrieved / len(relevant_ids),
                ndcg=dcg / idcg,
                hit=float(relevant_retrieved > 0),
            )
        )
    return RetrievalMetrics(
        query_id=query_id,
        relevant_count=len(relevant_ids),
        retrieved_count=len(predicted_ids),
        reciprocal_rank=reciprocal_rank,
        at_cutoff=tuple(rows),
    )


def summarize(rows: tuple[RetrievalMetrics, ...]) -> AggregateMetrics:
    if not rows:
        raise ValueError("No hay consultas para resumir")
    cutoffs = tuple(item.k for item in rows[0].at_cutoff)
    if any(tuple(item.k for item in row.at_cutoff) != cutoffs for row in rows):
        raise ValueError("Las consultas deben usar los mismos cutoffs")
    count = len(rows)
    aggregate = []
    for index, k in enumerate(cutoffs):
        values = tuple(row.at_cutoff[index] for row in rows)
        aggregate.append(
            CutoffMetrics(
                k=k,
                precision=math.fsum(value.precision for value in values) / count,
                recall=math.fsum(value.recall for value in values) / count,
                ndcg=math.fsum(value.ndcg for value in values) / count,
                hit=math.fsum(value.hit for value in values) / count,
            )
        )
    return AggregateMetrics(
        query_count=count,
        mean_reciprocal_rank=math.fsum(row.reciprocal_rank for row in rows) / count,
        at_cutoff=tuple(aggregate),
    )


def run_benchmark(
    *,
    mode: str,
    ranker: CandidateRanker,
    dataset: RetrievalDataset,
    cutoffs: tuple[int, ...] = (5, 10, 20),
    clock: Callable[[], float] = time.perf_counter,
) -> BenchmarkRun:
    if not mode or ranker.corpus_version != dataset.corpus_version:
        raise ValueError("Ranker incompatible con el corpus del benchmark")
    queries = []
    for case in dataset.cases:
        started = clock()
        ranking = ranker.rank(case.question, case.crop)
        elapsed_ms = (clock() - started) * 1000
        if elapsed_ms < 0:
            raise ValueError("Reloj no monotónico")
        predicted_ids = tuple(row.evidence_id for row in ranking)
        metrics = evaluate_ranking(
            case.query_id,
            predicted_ids,
            case.relevant_evidence_ids,
            cutoffs,
        )
        queries.append(QueryBenchmark(metrics, predicted_ids, elapsed_ms))
    query_rows = tuple(queries)
    latencies = tuple(sorted(query.latency_ms for query in query_rows))

    def percentile(fraction: float) -> float:
        position = (len(latencies) - 1) * fraction
        lower = math.floor(position)
        upper = math.ceil(position)
        if lower == upper:
            return latencies[lower]
        return latencies[lower] + (latencies[upper] - latencies[lower]) * (position - lower)

    return BenchmarkRun(
        mode=mode,
        corpus_version=dataset.corpus_version,
        dataset_sha256=dataset.file_sha256,
        queries=query_rows,
        summary=summarize(tuple(query.metrics for query in query_rows)),
        latency=LatencyMetrics(
            mean_ms=math.fsum(latencies) / len(latencies),
            p50_ms=percentile(0.5),
            p95_ms=percentile(0.95),
        ),
    )
