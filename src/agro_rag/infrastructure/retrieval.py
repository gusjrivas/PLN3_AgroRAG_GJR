import re
import unicodedata
from collections import Counter
from functools import lru_cache

from rank_bm25 import BM25Plus

from agro_rag.application.retrieval_pipeline import ScoredId
from agro_rag.domain.evidence import Catalogue, Evidence

STOP = set("a de del la las el los y o en un una que como cual para por es se su al".split())


def tokens(text: str) -> list[str]:
    text = re.sub(r"^\s*\d{1,3}\s*[.)]\s+", "", text)
    normalized = unicodedata.normalize("NFKD", text.casefold())
    plain = "".join(char for char in normalized if not unicodedata.combining(char))
    return [word for word in re.findall(r"\w+", plain) if word not in STOP]


class LexicalRetriever:
    """Explicit baseline, not a semantic index. Cache belongs to this snapshot only."""

    def __init__(self, catalogue: Catalogue) -> None:
        self.corpus_version = catalogue.version
        self.items = catalogue.evidence
        self.terms = [tokens(item.section + " " + item.text) for item in self.items]
        self.index = BM25Plus(self.terms) if self.items else None
        self._cached = lru_cache(maxsize=128)(self._search)

    def search(self, question: str, crop: str | None) -> tuple[Evidence, ...]:
        return self._cached(question, crop)

    def rank(self, question: str, crop: str | None) -> tuple[ScoredId, ...]:
        query = tokens(question)
        if not query or self.index is None:
            return ()
        scores = self.index.get_scores(query)
        indices = sorted(
            range(len(self.items)), key=lambda i: (-scores[i], self.items[i].evidence_id)
        )
        ranked = []
        for i in indices:
            item = self.items[i]
            if crop and item.crop not in (None, crop):
                continue
            if not set(query).intersection(self.terms[i]):
                continue
            ranked.append(ScoredId(item.evidence_id, float(scores[i])))
        return tuple(ranked)

    def _search(self, question: str, crop: str | None) -> tuple[Evidence, ...]:
        items = {item.evidence_id: item for item in self.items}
        selected = []
        counts: Counter[str] = Counter()
        for row in self.rank(question, crop):
            item = items[row.evidence_id]
            if counts[item.source_id] >= 2:
                continue
            selected.append(item)
            counts[item.source_id] += 1
            if len(selected) == 4:
                break
        return tuple(selected)
