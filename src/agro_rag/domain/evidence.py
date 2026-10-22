from dataclasses import dataclass


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


@dataclass(frozen=True)
class Catalogue:
    version: str
    evidence: tuple[Evidence, ...]
