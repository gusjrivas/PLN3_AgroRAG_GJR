from agro_rag.evaluation.benchmark import (
    BenchmarkCase,
    BenchmarkDataset,
    Category,
    ExpectedStatus,
    Split,
)
from scripts.run_e1_retrieval import select_ir_cases


def test_eva_02_e1_selects_only_reviewed_respondable_dev_cases() -> None:
    def case(
        query_id: str, *, split: Split = "dev", category: Category = "respondable"
    ) -> BenchmarkCase:
        expected_status: ExpectedStatus = (
            "answered" if category == "respondable" else "insufficient_evidence"
        )
        return BenchmarkCase(
            query_id=query_id,
            family_id=f"family-{query_id}",
            question=f"Pregunta {query_id}",
            crop="lettuce",
            category=category,
            expected_status=expected_status,
            reference_answer="Referencia" if category == "respondable" else "",
            required_claims=("Claim",) if category == "respondable" else (),
            relevant_evidence_ids=frozenset({"evidence"})
            if category == "respondable"
            else frozenset(),
            source_pages=("source:1",) if category == "respondable" else (),
            split=split,
            annotator="reviewer",
            review_status="reviewed",
            corpus_version="corpus-v1",
        )

    benchmark = BenchmarkDataset(
        corpus_version="corpus-v1",
        file_sha256="a" * 64,
        cases=tuple(case(f"dev-r-{index:03d}") for index in range(1, 19))
        + (case("test-r-001", split="test"), case("dev-u-001", category="unsupported")),
    )

    dataset = select_ir_cases(benchmark, split="dev")

    assert len(dataset.cases) == 18
    assert dataset.is_human_reviewed is True
    assert dataset.file_sha256 == benchmark.file_sha256
    assert {case.query_id for case in dataset.cases} == {
        item.query_id
        for item in benchmark.cases
        if item.split == "dev" and item.category == "respondable"
    }
