from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, allow_inf_nan=False)


class Measurement(Input):
    value: float = Field(strict=True)
    unit: str = Field(min_length=1, max_length=32)
    measurement_type: Literal["volumetric_water_content", "matric_potential", "unknown"]

    @model_validator(mode="after")
    def units(self) -> Self:
        if self.measurement_type == "volumetric_water_content":
            if self.unit not in ("%", "m3/m3"):
                raise ValueError("Unidad de contenido volumétrico inválida")
            if not 0 <= self.value <= (100 if self.unit == "%" else 1):
                raise ValueError("Contenido volumétrico fuera de rango")
        if self.measurement_type == "matric_potential" and self.unit not in ("kPa", "MPa"):
            raise ValueError("Unidad de potencial inválida")
        return self


class Context(Input):
    growth_stage: str | None = Field(default=None, max_length=500)
    soil_description: str | None = Field(default=None, max_length=500)
    measurement: Measurement | None = None


class Clarification(Input):
    original_question: str = Field(min_length=1, max_length=2000)
    answers: list[str] = Field(max_length=3)

    @model_validator(mode="after")
    def limits(self) -> Self:
        if any(not value.strip() or len(value) > 500 for value in self.answers):
            raise ValueError("Respuesta de aclaración inválida")
        return self


class QueryRequest(Input):
    question: str = Field(min_length=1, max_length=2000)
    crop: Literal["tomato", "lettuce"] | None = None
    context: Context | None = None
    clarification_context: Clarification | None = None


class ClaimResponse(BaseModel):
    claim_id: str
    text: str
    evidence_ids: list[str] = Field(min_length=1)


class CitationResponse(BaseModel):
    evidence_id: str
    source_id: str
    title: str
    edition: str
    pdf_page: int
    printed_page: str
    section: str
    excerpt: str
    source_url: str


class VerificationResponse(BaseModel):
    decision: Literal["approve", "revise", "clarify", "abstain"]
    revision_count: int = Field(ge=0, le=1)
    issue_codes: list[str]


class UsageResponse(BaseModel):
    llm_calls: int = Field(ge=0, le=6)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated: bool
    total_ms: int = Field(ge=0)
    cache_hit: bool


class QueryResponse(BaseModel):
    request_id: str
    status: Literal["answered", "needs_clarification", "insufficient_evidence"]
    answer: str
    claims: list[ClaimResponse]
    citations: list[CitationResponse]
    missing_information: list[str]
    limitations: list[str]
    corpus_version: str
    verification: VerificationResponse
    usage: UsageResponse

    @model_validator(mode="after")
    def consistency(self) -> Self:
        known = {c.evidence_id for c in self.citations}
        if self.status == "answered" and (
            not self.claims or any(not set(c.evidence_ids).issubset(known) for c in self.claims)
        ):
            raise ValueError("Respuesta sin citas")
        if self.status == "needs_clarification" and not self.missing_information:
            raise ValueError("Aclaración vacía")
        return self
