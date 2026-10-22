from typing import Protocol

from agro_rag.domain.evidence import Evidence


class Retriever(Protocol):
    def search(self, question: str, crop: str | None) -> tuple[Evidence, ...]: ...


def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> list[str]:
    if k <= 0:
        raise ValueError("k debe ser positivo")
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(dict.fromkeys(ranking), 1):
            scores[item] = scores.get(item, 0.0) + 1 / (k + rank)
    return sorted(scores, key=lambda item: (-scores[item], item))
