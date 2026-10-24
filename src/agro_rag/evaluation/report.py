"""Reproducible EVA-02 reports with explicit provenance and denominators."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

Dimension = Literal["retrieval", "generation", "agents", "operation"]
ExecutionKind = Literal["real", "test_double"]
ComparisonDirection = Literal["improved", "tied", "worse"]

_DIMENSIONS = {"retrieval", "generation", "agents", "operation"}
_EXPERIMENT_VARIANTS = {
    "E1": ("bm25", "vector", "hybrid", "hybrid_rerank"),
    "E2": ("without_verifier", "with_verifier"),
    "E3": ("cache_cold", "cache_hot"),
}


def _present(value: str) -> bool:
    return bool(value.strip())


@dataclass(frozen=True)
class MetricObservation:
    dimension: Dimension
    name: str
    value: float
    higher_is_better: bool

    def __post_init__(self) -> None:
        if (
            self.dimension not in _DIMENSIONS
            or not _present(self.name)
            or not math.isfinite(self.value)
        ):
            raise ValueError("Métrica EVA-02 inválida")


@dataclass(frozen=True)
class QueryObservation:
    query_id: str
    variant: str
    execution_kind: ExecutionKind
    corpus_version: str
    dataset_sha256: str
    commit_sha: str
    prompt_version: str
    model_versions: tuple[str, ...]
    status: str
    error_type: str | None
    input_tokens: int
    output_tokens: int
    latency_ms: float
    human_reviewed: bool
    metrics: tuple[MetricObservation, ...]

    def __post_init__(self) -> None:
        strings = (
            self.query_id,
            self.variant,
            self.corpus_version,
            self.prompt_version,
            self.status,
        )
        if (
            any(not _present(value) for value in strings)
            or self.execution_kind not in ("real", "test_double")
            or len(self.dataset_sha256) != 64
            or any(character not in "0123456789abcdef" for character in self.dataset_sha256)
            or len(self.commit_sha) != 40
            or any(character not in "0123456789abcdef" for character in self.commit_sha)
            or not self.model_versions
            or any(not _present(value) for value in self.model_versions)
            or len(self.model_versions) != len(set(self.model_versions))
            or self.input_tokens < 0
            or self.output_tokens < 0
            or not math.isfinite(self.latency_ms)
            or self.latency_ms < 0
        ):
            raise ValueError("Observación EVA-02 inválida")
        metric_ids = tuple((metric.dimension, metric.name) for metric in self.metrics)
        if len(metric_ids) != len(set(metric_ids)):
            raise ValueError("Métricas duplicadas en una observación")
        if self.status == "operational_error":
            if self.error_type is None or not _present(self.error_type) or self.metrics:
                raise ValueError("Un error operacional exige tipo y no admite métricas")
        elif self.error_type is not None or not self.metrics:
            raise ValueError("Un resultado exitoso exige métricas y no admite error")


@dataclass(frozen=True)
class MetricSummary:
    mean: float
    denominator: int
    higher_is_better: bool


@dataclass(frozen=True)
class VariantSummary:
    query_count: int
    error_count: int
    input_tokens: int
    output_tokens: int
    p50_ms: float
    p95_ms: float
    metrics: dict[str, MetricSummary]


@dataclass(frozen=True)
class PairedComparison:
    baseline: str
    candidate: str
    dimension: Dimension
    metric: str
    baseline_mean: float
    candidate_mean: float
    raw_delta: float
    direction: ComparisonDirection
    metric_denominator: int
    excluded_query_ids: tuple[str, ...]


@dataclass(frozen=True)
class EvaluationReport:
    experiment_id: str
    execution_kind: ExecutionKind
    corpus_version: str
    dataset_sha256: str
    commit_sha: str
    primary_dimension: Dimension
    primary_metric: str
    query_ids: tuple[str, ...]
    observations: tuple[QueryObservation, ...]
    summaries: dict[str, VariantSummary]
    comparisons: tuple[PairedComparison, ...]


def _percentile(values: tuple[float, ...], fraction: float) -> float:
    ordered = tuple(sorted(values))
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _metric_map(row: QueryObservation) -> dict[tuple[str, str], MetricObservation]:
    return {(metric.dimension, metric.name): metric for metric in row.metrics}


def _summarize(rows: tuple[QueryObservation, ...]) -> VariantSummary:
    metric_values: dict[tuple[str, str], list[MetricObservation]] = {}
    for row in rows:
        for metric in row.metrics:
            metric_values.setdefault((metric.dimension, metric.name), []).append(metric)
    metrics = {}
    for (dimension, name), values in sorted(metric_values.items()):
        directions = {value.higher_is_better for value in values}
        if len(directions) != 1:
            raise ValueError("Una métrica no puede cambiar su dirección")
        metrics[f"{dimension}.{name}"] = MetricSummary(
            mean=math.fsum(value.value for value in values) / len(values),
            denominator=len(values),
            higher_is_better=values[0].higher_is_better,
        )
    latencies = tuple(row.latency_ms for row in rows)
    return VariantSummary(
        query_count=len(rows),
        error_count=sum(row.status == "operational_error" for row in rows),
        input_tokens=sum(row.input_tokens for row in rows),
        output_tokens=sum(row.output_tokens for row in rows),
        p50_ms=_percentile(latencies, 0.5),
        p95_ms=_percentile(latencies, 0.95),
        metrics=metrics,
    )


def build_report(
    *,
    experiment_id: str,
    observations: tuple[QueryObservation, ...],
    primary_metric: tuple[Dimension, str],
) -> EvaluationReport:
    """Build one complete, paired E1/E2/E3 comparison without dropping failures."""
    expected_variants = _EXPERIMENT_VARIANTS.get(experiment_id)
    if expected_variants is None or not observations:
        raise ValueError("Experimento EVA-02 inválido o vacío")
    dimension, metric_name = primary_metric
    if dimension not in _DIMENSIONS or not _present(metric_name):
        raise ValueError("Métrica primaria inválida")

    kinds = {row.execution_kind for row in observations}
    if len(kinds) != 1:
        raise ValueError("No se pueden mezclar ejecuciones reales y dobles")
    execution_kind = next(iter(kinds))
    if execution_kind == "real" and any(not row.human_reviewed for row in observations):
        raise ValueError("Una ejecución real exige revisión humana")

    common = {(row.corpus_version, row.dataset_sha256, row.commit_sha) for row in observations}
    if len(common) != 1:
        raise ValueError("La comparación exige corpus, dataset y commit congelados")
    corpus_version, dataset_sha256, commit_sha = next(iter(common))

    variants = {row.variant for row in observations}
    if variants != set(expected_variants):
        raise ValueError("El experimento no contiene todas sus variantes congeladas")
    grouped = {
        variant: tuple(row for row in observations if row.variant == variant)
        for variant in expected_variants
    }
    for variant, rows in grouped.items():
        identities = tuple(row.query_id for row in rows)
        if len(identities) != len(set(identities)):
            raise ValueError(f"query_id duplicado en {variant}")
        configurations = {(row.prompt_version, row.model_versions) for row in rows}
        if len(configurations) != 1:
            raise ValueError(f"Configuración no congelada en {variant}")
    query_sets = {frozenset(row.query_id for row in rows) for rows in grouped.values()}
    if len(query_sets) != 1:
        raise ValueError("Las variantes deben usar consultas pareadas")
    query_ids = tuple(sorted(next(iter(query_sets))))

    baseline = expected_variants[0]
    baseline_by_id = {row.query_id: row for row in grouped[baseline]}
    comparisons = []
    for candidate in expected_variants[1:]:
        candidate_by_id = {row.query_id: row for row in grouped[candidate]}
        paired_values = []
        excluded = []
        direction_flags: set[bool] = set()
        for query_id in query_ids:
            baseline_value = _metric_map(baseline_by_id[query_id]).get(primary_metric)
            candidate_value = _metric_map(candidate_by_id[query_id]).get(primary_metric)
            if baseline_value is None or candidate_value is None:
                excluded.append(query_id)
                continue
            direction_flags.update(
                (baseline_value.higher_is_better, candidate_value.higher_is_better)
            )
            paired_values.append((baseline_value.value, candidate_value.value))
        if not paired_values or len(direction_flags) != 1:
            raise ValueError("Métrica primaria ausente o con dirección inconsistente")
        baseline_mean = math.fsum(value[0] for value in paired_values) / len(paired_values)
        candidate_mean = math.fsum(value[1] for value in paired_values) / len(paired_values)
        raw_delta = candidate_mean - baseline_mean
        improvement = raw_delta if next(iter(direction_flags)) else -raw_delta
        comparison_direction: ComparisonDirection = (
            "improved" if improvement > 0 else "worse" if improvement < 0 else "tied"
        )
        comparisons.append(
            PairedComparison(
                baseline=baseline,
                candidate=candidate,
                dimension=dimension,
                metric=metric_name,
                baseline_mean=baseline_mean,
                candidate_mean=candidate_mean,
                raw_delta=raw_delta,
                direction=comparison_direction,
                metric_denominator=len(paired_values),
                excluded_query_ids=tuple(excluded),
            )
        )

    return EvaluationReport(
        experiment_id=experiment_id,
        execution_kind=execution_kind,
        corpus_version=corpus_version,
        dataset_sha256=dataset_sha256,
        commit_sha=commit_sha,
        primary_dimension=dimension,
        primary_metric=metric_name,
        query_ids=query_ids,
        observations=observations,
        summaries={variant: _summarize(rows) for variant, rows in grouped.items()},
        comparisons=tuple(comparisons),
    )


def write_report(path: Path, report: EvaluationReport) -> None:
    """Persist the complete report; callers choose a versioned run directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(report), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
