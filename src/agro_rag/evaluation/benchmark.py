"""Frozen contract for the human-reviewed EVA-01 benchmark."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from agro_rag.domain.evidence import Catalogue

Split = Literal["dev", "test"]
Category = Literal["respondable", "unsupported", "adversarial"]
ExpectedStatus = Literal["answered", "needs_clarification", "insufficient_evidence"]
ReviewStatus = Literal["reviewed", "pending_human"]


@dataclass(frozen=True)
class BenchmarkCase:
    query_id: str
    family_id: str
    question: str
    crop: Literal["tomato", "lettuce"] | None
    category: Category
    expected_status: ExpectedStatus
    reference_answer: str
    required_claims: tuple[str, ...]
    relevant_evidence_ids: frozenset[str]
    source_pages: tuple[str, ...]
    split: Split
    annotator: str
    review_status: ReviewStatus
    corpus_version: str


@dataclass(frozen=True)
class BenchmarkDataset:
    corpus_version: str
    file_sha256: str
    cases: tuple[BenchmarkCase, ...]

    @property
    def split_counts(self) -> dict[str, int]:
        return dict(Counter(case.split for case in self.cases))

    @property
    def category_counts(self) -> dict[str, int]:
        return dict(Counter(case.category for case in self.cases))

    @property
    def ir_cases(self) -> tuple[BenchmarkCase, ...]:
        return tuple(case for case in self.cases if case.category == "respondable")

    @property
    def abstention_cases(self) -> tuple[BenchmarkCase, ...]:
        return tuple(case for case in self.cases if case.category != "respondable")


@dataclass(frozen=True)
class BenchmarkDraft:
    corpus_version: str
    file_sha256: str
    cases: tuple[BenchmarkCase, ...]

    @property
    def split_counts(self) -> dict[str, int]:
        return dict(Counter(case.split for case in self.cases))

    @property
    def category_counts(self) -> dict[str, int]:
        return dict(Counter(case.category for case in self.cases))

    @property
    def pending_human_count(self) -> int:
        return sum(case.review_status == "pending_human" for case in self.cases)


_CASE_FIELDS = {
    "query_id",
    "family_id",
    "question",
    "crop",
    "category",
    "expected_status",
    "reference_answer",
    "required_claims",
    "relevant_evidence_ids",
    "source_pages",
    "split",
    "annotator",
    "review_status",
    "corpus_version",
}
_EXPECTED_STATUS: dict[Category, ExpectedStatus] = {
    "respondable": "answered",
    "unsupported": "insufficient_evidence",
    "adversarial": "needs_clarification",
}
_EXPECTED_PER_SPLIT = {"respondable": 18, "unsupported": 6, "adversarial": 6}


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: object, *, allow_empty: bool) -> tuple[str, ...]:
    if (
        not isinstance(value, list)
        or (not allow_empty and not value)
        or any(not _nonempty_string(item) for item in value)
        or len(value) != len(set(value))
    ):
        raise ValueError("Lista contractual invalida")
    return tuple(cast(list[str], value))


def _case_from_json(
    value: object,
    catalogue: Catalogue,
    *,
    expected_review_status: ReviewStatus,
) -> BenchmarkCase:
    if not isinstance(value, Mapping) or set(value) != _CASE_FIELDS:
        raise ValueError("Caso de benchmark con campos invalidos")

    query_id = value["query_id"]
    family_id = value["family_id"]
    question = value["question"]
    crop = value["crop"]
    category = value["category"]
    expected_status = value["expected_status"]
    reference_answer = value["reference_answer"]
    split = value["split"]
    annotator = value["annotator"]
    review_status = value["review_status"]
    corpus_version = value["corpus_version"]
    if (
        not _nonempty_string(query_id)
        or not _nonempty_string(family_id)
        or not _nonempty_string(question)
        or crop not in (None, "tomato", "lettuce")
        or category not in _EXPECTED_STATUS
        or expected_status != _EXPECTED_STATUS[cast(Category, category)]
        or not isinstance(reference_answer, str)
        or split not in ("dev", "test")
        or not _nonempty_string(annotator)
        or corpus_version != catalogue.version
    ):
        raise ValueError("Caso de benchmark invalido o de otro corpus")
    if review_status != expected_review_status:
        raise ValueError(f"review_status debe ser {expected_review_status}")

    required_claims = _string_list(value["required_claims"], allow_empty=True)
    relevant = _string_list(value["relevant_evidence_ids"], allow_empty=True)
    source_pages = _string_list(value["source_pages"], allow_empty=True)
    items = {item.evidence_id: item for item in catalogue.evidence}
    if any(item_id not in items for item_id in relevant):
        raise ValueError("ID de evidencia no resoluble en el catalogo")
    if crop and any(items[item_id].crop not in (None, crop) for item_id in relevant):
        raise ValueError("Evidencia incompatible con el cultivo")

    if category == "respondable":
        if not reference_answer.strip() or not required_claims or not relevant or not source_pages:
            raise ValueError("Caso respondible sin referencia o evidencia completa")
    elif reference_answer or required_claims or relevant or source_pages:
        raise ValueError("Caso sin soporte no puede entrar al denominador IR")

    return BenchmarkCase(
        query_id=cast(str, query_id),
        family_id=cast(str, family_id),
        question=cast(str, question),
        crop=cast(Literal["tomato", "lettuce"] | None, crop),
        category=cast(Category, category),
        expected_status=cast(ExpectedStatus, expected_status),
        reference_answer=reference_answer,
        required_claims=required_claims,
        relevant_evidence_ids=frozenset(relevant),
        source_pages=source_pages,
        split=cast(Split, split),
        annotator=cast(str, annotator),
        review_status=expected_review_status,
        corpus_version=catalogue.version,
    )


def _load_values(path: Path) -> tuple[bytes, list[object]]:
    raw = path.read_bytes()
    try:
        values = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("JSONL de benchmark invalido") from exc
    return raw, values


def _validate_sampling_contract(cases: tuple[BenchmarkCase, ...]) -> None:
    if len(cases) != 60 or len({case.query_id for case in cases}) != len(cases):
        raise ValueError("EVA-01 exige 60 query_id unicos")

    family_splits: dict[str, Split] = {}
    for case in cases:
        previous = family_splits.setdefault(case.family_id, case.split)
        if previous != case.split:
            raise ValueError("Una familia de consultas no puede cruzar splits")

    for split in ("dev", "test"):
        subset = tuple(case for case in cases if case.split == split)
        if len(subset) != 30 or Counter(case.category for case in subset) != _EXPECTED_PER_SPLIT:
            raise ValueError("Cada split exige 18 respondibles, 6 sin soporte y 6 adversariales")


def load_benchmark(path: Path, catalogue: Catalogue) -> BenchmarkDataset:
    """Load human-reviewed EVA-01 JSONL and reject sampling or review drift."""
    raw, values = _load_values(path)
    cases = tuple(
        _case_from_json(value, catalogue, expected_review_status="reviewed") for value in values
    )
    _validate_sampling_contract(cases)

    return BenchmarkDataset(
        corpus_version=catalogue.version,
        file_sha256=hashlib.sha256(raw).hexdigest(),
        cases=cases,
    )


def load_benchmark_draft(path: Path, catalogue: Catalogue) -> BenchmarkDraft:
    """Validate a complete annotation packet without treating it as reviewed evidence."""
    raw, values = _load_values(path)
    cases = tuple(
        _case_from_json(value, catalogue, expected_review_status="pending_human")
        for value in values
    )
    _validate_sampling_contract(cases)
    return BenchmarkDraft(
        corpus_version=catalogue.version,
        file_sha256=hashlib.sha256(raw).hexdigest(),
        cases=cases,
    )
