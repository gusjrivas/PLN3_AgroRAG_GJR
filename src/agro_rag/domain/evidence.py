from dataclasses import dataclass
from typing import Literal, cast

SourceType = Literal["technical_manual", "technical_guide", "institutional_fact_sheet"]
GrowthStage = Literal[
    "establishment",
    "vegetative_growth",
    "flowering",
    "fruit_set",
    "fruit_development",
    "pre_harvest",
]
ApplicableRegion = Literal["ar-mendoza-oasis-norte"]
Applicability = Literal["general", "specific", "unknown"]

SOURCE_TYPES = frozenset({"technical_manual", "technical_guide", "institutional_fact_sheet"})
GROWTH_STAGES = frozenset(
    {
        "establishment",
        "vegetative_growth",
        "flowering",
        "fruit_set",
        "fruit_development",
        "pre_harvest",
    }
)
APPLICABLE_REGIONS = frozenset({"ar-mendoza-oasis-norte"})
APPLICABILITY_VALUES = frozenset({"general", "specific", "unknown"})


def _controlled_sequence(name: str, values: object, allowed: frozenset[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, (list, tuple)):
        raise ValueError(f"{name} debe ser una secuencia")
    if any(not isinstance(value, str) or value not in allowed for value in values):
        raise ValueError(f"{name} contiene un valor fuera del vocabulario")
    result = tuple(values)
    if len(result) != len(set(result)):
        raise ValueError(f"{name} contiene valores duplicados")
    return result


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    corpus_version: str
    source_id: str
    title: str
    edition: str
    source_url: str
    pdf_page: int
    printed_page: str
    section: str
    crop: str | None
    text: str
    original_text: str
    start: int
    end: int
    transformation: str = "verbatim"
    source_type: SourceType | None = None
    growth_stages: tuple[GrowthStage, ...] = ()
    applicable_regions: tuple[ApplicableRegion, ...] = ()
    applicability: Applicability = "unknown"

    def __post_init__(self) -> None:
        if self.source_type is not None and (
            not isinstance(self.source_type, str) or self.source_type not in SOURCE_TYPES
        ):
            raise ValueError("source_type fuera del vocabulario")
        if (
            not isinstance(self.applicability, str)
            or self.applicability not in APPLICABILITY_VALUES
        ):
            raise ValueError("applicability fuera del vocabulario")
        growth_stages = _controlled_sequence("growth_stages", self.growth_stages, GROWTH_STAGES)
        applicable_regions = _controlled_sequence(
            "applicable_regions", self.applicable_regions, APPLICABLE_REGIONS
        )
        # JSON persists tuples as arrays; restore the immutable domain representation.
        object.__setattr__(
            self, "growth_stages", cast(tuple[GrowthStage, ...], growth_stages)
        )
        object.__setattr__(
            self,
            "applicable_regions",
            cast(tuple[ApplicableRegion, ...], applicable_regions),
        )


@dataclass(frozen=True)
class Catalogue:
    version: str
    evidence: tuple[Evidence, ...]
