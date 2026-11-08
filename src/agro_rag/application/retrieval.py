from dataclasses import dataclass
from typing import Literal, Protocol, cast

from agro_rag.domain.evidence import (
    APPLICABLE_REGIONS,
    GROWTH_STAGES,
    ApplicableRegion,
    Evidence,
    GrowthStage,
)

Crop = Literal["tomato", "lettuce"]
Compatibility = Literal["exact", "general", "unknown", "incompatible"]


@dataclass(frozen=True)
class RetrievalFilters:
    crop: Crop | None = None
    growth_stage: GrowthStage | None = None
    region: ApplicableRegion | None = None

    def __post_init__(self) -> None:
        if self.crop is not None and (
            not isinstance(self.crop, str) or self.crop not in ("tomato", "lettuce")
        ):
            raise ValueError("crop fuera del vocabulario")
        if self.growth_stage is not None and (
            not isinstance(self.growth_stage, str) or self.growth_stage not in GROWTH_STAGES
        ):
            raise ValueError("growth_stage fuera del vocabulario")
        if self.region is not None and (
            not isinstance(self.region, str) or self.region not in APPLICABLE_REGIONS
        ):
            raise ValueError("region fuera del vocabulario")


type FilterInput = RetrievalFilters | str | None


def normalize_filters(value: FilterInput) -> RetrievalFilters:
    """Temporary crop-only compatibility until META-03 constructs structured filters."""
    if isinstance(value, RetrievalFilters):
        return value
    if value not in (None, "tomato", "lettuce"):
        raise ValueError("crop fuera del vocabulario")
    return RetrievalFilters(crop=cast(Crop | None, value))


def classify_evidence(item: Evidence, filters: RetrievalFilters) -> Compatibility:
    if filters.crop is not None and item.crop is not None and item.crop != filters.crop:
        return "incompatible"
    contextual = filters.growth_stage is not None or filters.region is not None
    if not contextual:
        return "exact"
    if (
        filters.growth_stage is not None
        and item.growth_stages
        and filters.growth_stage not in item.growth_stages
    ):
        return "incompatible"
    if (
        filters.region is not None
        and item.applicable_regions
        and filters.region not in item.applicable_regions
    ):
        return "incompatible"
    if item.applicability == "general":
        return "general"

    explicit_matches = []
    if filters.growth_stage is not None:
        explicit_matches.append(filters.growth_stage in item.growth_stages)
    if filters.region is not None:
        explicit_matches.append(filters.region in item.applicable_regions)
    if explicit_matches and all(explicit_matches):
        return "exact"
    return "unknown"


def prioritize_evidence(
    items: tuple[Evidence, ...], filters: RetrievalFilters
) -> tuple[tuple[Evidence, ...], tuple[str, ...]]:
    """Stable compatibility partition; provider order is retained inside every class."""
    buckets: dict[Compatibility, list[Evidence]] = {
        "exact": [],
        "general": [],
        "unknown": [],
        "incompatible": [],
    }
    for item in items:
        buckets[classify_evidence(item, filters)].append(item)
    compatible = (*buckets["exact"], *buckets["general"], *buckets["unknown"])
    excluded = tuple(item.evidence_id for item in buckets["incompatible"])
    return compatible, excluded


class Retriever(Protocol):
    def search(self, question: str, filters: FilterInput) -> tuple[Evidence, ...]: ...


def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> list[str]:
    if k <= 0:
        raise ValueError("k debe ser positivo")
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(dict.fromkeys(ranking), 1):
            scores[item] = scores.get(item, 0.0) + 1 / (k + rank)
    return sorted(scores, key=lambda item: (-scores[item], item))
