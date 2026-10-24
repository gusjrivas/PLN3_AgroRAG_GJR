"""Provider-independent ranking orchestration; no model or network I/O at import."""

import json
import math
from collections import Counter
from dataclasses import dataclass
from typing import Literal, Protocol

from agro_rag.domain.evidence import Catalogue, Evidence

Mode = Literal["bm25", "vector", "hybrid", "hybrid_rerank"]


@dataclass(frozen=True)
class ScoredId:
    evidence_id: str
    score: float


@dataclass(frozen=True)
class IndexIdentity:
    corpus_version: str
    model: str
    revision: str
    dimension: int


class CandidateRanker(Protocol):
    corpus_version: str

    def rank(self, question: str, crop: str | None) -> tuple[ScoredId, ...]: ...


class Reranker(Protocol):
    def rank(self, question: str, candidates: tuple[Evidence, ...]) -> tuple[ScoredId, ...]: ...


class TokenCounter(Protocol):
    """Adapter must count with the exact downstream model tokenizer, without truncation."""

    def count(self, text: str) -> int: ...


class RetrievalUnavailable(RuntimeError):
    pass


class RetrievalContractError(RuntimeError):
    pass


@dataclass(frozen=True)
class StageRanking:
    stage: str
    ranking: tuple[ScoredId, ...]


@dataclass(frozen=True)
class RetrievalResult:
    corpus_version: str
    mode: Mode
    evidence: tuple[Evidence, ...]
    context: str
    token_count: int
    stages: tuple[StageRanking, ...]
    excluded_ids: tuple[str, ...]


def serialize_context(items: tuple[Evidence, ...]) -> str:
    """Exact text counted for the evidence budget; complete prompts have separate budgets."""
    if not items:
        return ""
    return json.dumps(
        [
            dict(
                evidence_id=e.evidence_id,
                source_id=e.source_id,
                pdf_page=e.pdf_page,
                section=e.section,
                text=e.text,
            )
            for e in items
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )


class RetrievalPipeline:
    def __init__(
        self,
        *,
        catalogue: Catalogue,
        lexical: CandidateRanker,
        token_counter: TokenCounter,
        mode: Mode = "bm25",
        vector: CandidateRanker | None = None,
        expected_index: IndexIdentity | None = None,
        actual_index: IndexIdentity | None = None,
        reranker: Reranker | None = None,
        token_budget: int = 3000,
        source_cap: int = 2,
        max_items: int = 4,
        candidate_limit: int = 20,
    ) -> None:
        if mode not in ("bm25", "vector", "hybrid", "hybrid_rerank"):
            raise ValueError("Modo de recuperación inválido")
        if min(token_budget, source_cap, max_items, candidate_limit) <= 0:
            raise ValueError("Los límites deben ser positivos")
        self.items = {e.evidence_id: e for e in catalogue.evidence}
        if len(self.items) != len(catalogue.evidence) or any(
            e.corpus_version != catalogue.version for e in catalogue.evidence
        ):
            raise ValueError("Identidad inconsistente en catálogo")
        if lexical.corpus_version != catalogue.version or (
            mode != "bm25" and vector is not None and vector.corpus_version != catalogue.version
        ):
            raise ValueError("Ranker de otra versión")
        if mode != "bm25":
            if vector is None or expected_index is None or actual_index != expected_index:
                raise ValueError("Falta vector o identidad compatible del índice")
            if (
                expected_index.corpus_version != catalogue.version
                or not expected_index.model
                or not expected_index.revision
                or expected_index.dimension <= 0
            ):
                raise ValueError("Identidad del índice inválida")
        if mode == "hybrid_rerank" and reranker is None:
            raise ValueError("Falta reranker")
        self.version = catalogue.version
        self.mode = mode
        self.lexical, self.vector, self.reranker = lexical, vector, reranker
        self.token_counter = token_counter
        self.token_budget, self.source_cap = token_budget, source_cap
        self.max_items, self.candidate_limit = max_items, candidate_limit

    def search(self, question: str, crop: str | None) -> tuple[Evidence, ...]:
        return self.retrieve(question, crop).evidence

    @property
    def corpus_version(self) -> str:
        return self.version

    def _normalize(self, rows: tuple[ScoredId, ...]) -> tuple[ScoredId, ...]:
        if any(not row.evidence_id or not math.isfinite(row.score) for row in rows):
            raise RetrievalContractError("Ranking con ID o score inválido")
        # Collapse duplicates by best score, then tie-break by stable evidence ID.
        best: dict[str, float] = {}
        for row in rows:
            best[row.evidence_id] = max(best.get(row.evidence_id, -math.inf), row.score)
        return tuple(
            ScoredId(id, score)
            for id, score in sorted(best.items(), key=lambda item: (-item[1], item[0]))
        )

    def _rank_candidates(
        self, question: str, crop: str | None
    ) -> tuple[tuple[ScoredId, ...], tuple[StageRanking, ...], tuple[str, ...]]:
        stages: list[StageRanking] = []
        excluded: set[str] = set()
        rankings: list[tuple[ScoredId, ...]] = []
        providers: list[tuple[str, CandidateRanker | None]] = []
        if self.mode != "vector":
            providers.append(("bm25", self.lexical))
        if self.mode != "bm25":
            providers.append(("vector", self.vector))
        for name, provider in providers if question.strip() else []:
            assert provider is not None  # validated at construction
            try:
                rows = provider.rank(question, crop)
            except Exception as exc:
                raise RetrievalUnavailable(f"Proveedor {name} no disponible") from exc
            valid = []
            for row in self._normalize(rows):
                item = self.items.get(row.evidence_id)
                if item is None or (crop and item.crop not in (None, crop)):
                    excluded.add(row.evidence_id)
                else:
                    valid.append(row)
            ranking = tuple(valid[: self.candidate_limit])
            rankings.append(ranking)
            stages.append(StageRanking(name, ranking))
        ordered = rankings[0] if rankings else ()
        if len(rankings) == 2:
            scores: dict[str, float] = {}
            for ranking in rankings:
                for rank, row in enumerate(ranking, 1):
                    scores[row.evidence_id] = scores.get(row.evidence_id, 0.0) + 1 / (60 + rank)
            ordered = self._normalize(tuple(ScoredId(id, score) for id, score in scores.items()))
            ordered = ordered[: self.candidate_limit]
            stages.append(StageRanking("rrf", ordered))
        if self.mode == "hybrid_rerank" and ordered:
            assert self.reranker is not None
            candidates = tuple(self.items[row.evidence_id] for row in ordered)
            try:
                reranked = self.reranker.rank(question, candidates)
            except Exception as exc:
                raise RetrievalUnavailable("Proveedor reranker no disponible") from exc
            ordered = self._normalize(reranked)
            if {r.evidence_id for r in ordered} != {e.evidence_id for e in candidates}:
                raise RetrievalContractError("El reranker debe puntuar exactamente los candidatos")
            stages.append(StageRanking("reranker", ordered))
        return ordered, tuple(stages), tuple(sorted(excluded))

    def rank(self, question: str, crop: str | None) -> tuple[ScoredId, ...]:
        """Return final candidates for evaluation without invoking context tokenization."""
        return self._rank_candidates(question, crop)[0]

    def retrieve(self, question: str, crop: str | None) -> RetrievalResult:
        ordered, stages, excluded = self._rank_candidates(question, crop)
        selected: list[Evidence] = []
        count = 0
        counts: Counter[str] = Counter()
        for row in ordered:
            item = self.items[row.evidence_id]
            if counts[item.source_id] >= self.source_cap:
                continue
            text = serialize_context((*selected, item))
            try:
                new_count = self.token_counter.count(text)
            except Exception as exc:
                raise RetrievalUnavailable("Proveedor tokenizer no disponible") from exc
            if not isinstance(new_count, int) or isinstance(new_count, bool) or new_count <= 0:
                raise RetrievalContractError("El tokenizer devolvió un recuento inválido")
            if new_count > self.token_budget:
                continue
            selected.append(item)
            count = new_count
            counts[item.source_id] += 1
            if len(selected) == self.max_items:
                break
        evidence = tuple(selected)
        return RetrievalResult(
            self.version,
            self.mode,
            evidence,
            serialize_context(evidence),
            count,
            stages,
            excluded,
        )
