"""Cross-encoder adapter derived from the Teoria1 RAG reranker."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from importlib import import_module
from typing import Protocol

from agro_rag.application.retrieval_pipeline import ScoredId
from agro_rag.domain.evidence import Evidence


class CrossEncoderModel(Protocol):
    def predict(self, pairs: list[tuple[str, str]]) -> object: ...


@dataclass(frozen=True)
class CrossEncoderReranker:
    model: CrossEncoderModel
    model_name: str
    revision: str

    def __post_init__(self) -> None:
        if not self.model_name or not self.revision:
            raise ValueError("Identidad inválida del reranker")

    @classmethod
    def load(
        cls,
        *,
        model_name: str,
        revision: str,
        device: str | None = None,
        local_files_only: bool = False,
    ) -> CrossEncoderReranker:
        sentence_transformers = import_module("sentence_transformers")
        model = sentence_transformers.CrossEncoder(
            model_name,
            revision=revision,
            device=device,
            local_files_only=local_files_only,
            trust_remote_code=False,
        )
        return cls(model=model, model_name=model_name, revision=revision)

    def rank(
        self,
        question: str,
        candidates: tuple[Evidence, ...],
    ) -> tuple[ScoredId, ...]:
        if not candidates:
            return ()
        scores = self.model.predict([(question, candidate.text) for candidate in candidates])
        if not isinstance(scores, Iterable) or isinstance(scores, (str, bytes)):
            raise ValueError("Respuesta inválida del reranker")
        try:
            values = [float(value) for value in scores]
        except (TypeError, ValueError) as exc:
            raise ValueError("Respuesta inválida del reranker") from exc
        if len(values) != len(candidates) or any(not math.isfinite(value) for value in values):
            raise ValueError("Respuesta inválida del reranker")
        return tuple(
            ScoredId(candidate.evidence_id, score)
            for candidate, score in zip(candidates, values, strict=True)
        )
