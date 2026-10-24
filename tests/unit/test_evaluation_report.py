import json
from dataclasses import replace

import pytest


def observations(*, candidate_values=(0.70, 0.75), execution_kind="real"):
    from agro_rag.evaluation.report import MetricObservation, QueryObservation

    rows = []
    values = {
        "without_verifier": (0.80, 0.90),
        "with_verifier": candidate_values,
    }
    for variant, factual_support in values.items():
        for index, value in enumerate(factual_support, 1):
            rows.append(
                QueryObservation(
                    query_id=f"q{index}",
                    variant=variant,
                    execution_kind=execution_kind,
                    corpus_version="corpus-v1",
                    dataset_sha256="a" * 64,
                    commit_sha="b" * 40,
                    prompt_version="prompt-v1",
                    model_versions=("generator:model-v1", "verifier:model-v1"),
                    status="answered",
                    error_type=None,
                    input_tokens=100 + index,
                    output_tokens=20 + index,
                    latency_ms=10.0 * index,
                    human_reviewed=True,
                    metrics=(
                        MetricObservation("retrieval", "recall@20", 0.9, True),
                        MetricObservation("generation", "factual_support", value, True),
                        MetricObservation("agents", "verifier_correct", value, True),
                        MetricObservation("operation", "estimated_cost", 0.01, False),
                    ),
                )
            )
        rows.append(
            QueryObservation(
                query_id="q-error",
                variant=variant,
                execution_kind=execution_kind,
                corpus_version="corpus-v1",
                dataset_sha256="a" * 64,
                commit_sha="b" * 40,
                prompt_version="prompt-v1",
                model_versions=("generator:model-v1", "verifier:model-v1"),
                status="operational_error",
                error_type="TimeoutError",
                input_tokens=12,
                output_tokens=0,
                latency_ms=60_000.0,
                human_reviewed=True,
                metrics=(),
            )
        )
    return tuple(rows)


def test_eva_02_comparacion_preserves_provenance_denominators_and_errors(tmp_path):
    from agro_rag.evaluation.report import build_report, write_report

    report = build_report(
        experiment_id="E2",
        observations=observations(candidate_values=(0.95, 0.95)),
        primary_metric=("generation", "factual_support"),
    )

    assert report.execution_kind == "real"
    assert report.query_ids == ("q-error", "q1", "q2")
    assert report.summaries["with_verifier"].query_count == 3
    assert report.summaries["with_verifier"].error_count == 1
    assert report.summaries["with_verifier"].p50_ms == 20.0
    assert report.summaries["with_verifier"].p95_ms == pytest.approx(54_002.0)
    comparison = report.comparisons[0]
    assert comparison.metric_denominator == 2
    assert comparison.excluded_query_ids == ("q-error",)
    assert comparison.direction == "improved"

    target = tmp_path / "e2-report.json"
    write_report(target, report)
    saved = json.loads(target.read_text(encoding="utf-8"))
    assert len(saved["observations"]) == 6
    assert saved["observations"][2]["error_type"] == "TimeoutError"
    assert saved["summaries"]["with_verifier"]["input_tokens"] == 215


def test_eva_02_negativo_is_reported_without_cherry_picking():
    from agro_rag.evaluation.report import build_report

    report = build_report(
        experiment_id="E2",
        observations=observations(candidate_values=(0.70, 0.75)),
        primary_metric=("generation", "factual_support"),
    )

    comparison = report.comparisons[0]
    assert comparison.candidate == "with_verifier"
    assert comparison.raw_delta == pytest.approx(-0.125)
    assert comparison.direction == "worse"
    assert comparison.metric_denominator == 2
    assert report.summaries["with_verifier"].query_count == 3


def test_eva_02_rejects_unpaired_or_mixed_provenance():
    from agro_rag.evaluation.report import build_report

    rows = observations()
    with pytest.raises(ValueError, match="pareadas"):
        build_report(
            experiment_id="E2",
            observations=rows[:-1],
            primary_metric=("generation", "factual_support"),
        )

    mixed = rows[:-1] + (replace(rows[-1], execution_kind="test_double"),)
    with pytest.raises(ValueError, match="mezclar"):
        build_report(
            experiment_id="E2",
            observations=mixed,
            primary_metric=("generation", "factual_support"),
        )
