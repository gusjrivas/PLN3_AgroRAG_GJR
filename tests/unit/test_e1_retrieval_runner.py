from pathlib import Path

from agro_rag.evaluation.benchmark import load_benchmark
from agro_rag.infrastructure.corpus import load_catalogue
from scripts.run_e1_retrieval import select_ir_cases


def test_eva_02_e1_selects_only_reviewed_respondable_dev_cases() -> None:
    catalogue = load_catalogue(Path("data/processed/catalogue"))
    benchmark = load_benchmark(Path("data/evaluation/benchmark-60.jsonl"), catalogue)

    dataset = select_ir_cases(benchmark, split="dev")

    assert len(dataset.cases) == 18
    assert dataset.is_human_reviewed is True
    assert dataset.file_sha256 == benchmark.file_sha256
    assert {case.query_id for case in dataset.cases} == {
        case.query_id
        for case in benchmark.cases
        if case.split == "dev" and case.category == "respondable"
    }
