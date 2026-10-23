"""Curated, offline PDF admission. Never downloads or executes source content."""

import hashlib
import json
import os
import re
import sqlite3
import tempfile
from contextlib import closing
from dataclasses import asdict
from pathlib import Path
from typing import Literal

import pdfplumber
from pydantic import BaseModel, ConfigDict, Field

from agro_rag.domain.evidence import Catalogue, Evidence


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Table(StrictModel):
    headers: list[str] = Field(min_length=1)
    rows: list[list[str]] = Field(min_length=1)
    reviewed: Literal[True]


class Page(StrictModel):
    pdf_page: int = Field(ge=1)
    printed_page: str = Field(min_length=1)
    section: str = Field(min_length=1)
    crop: Literal["tomato", "lettuce"] | None = None
    start_marker: str | None = None
    end_marker: str | None = None
    table: Table | None = None


class Source(StrictModel):
    source_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    authors: list[str] = Field(min_length=1)
    institution: str = Field(min_length=1)
    edition: str = Field(min_length=1)
    language: Literal["es", "en"]
    source_url: str = Field(pattern=r"^https://")
    access_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    local_file: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    rights_status: Literal["public_access_no_redistribution", "synthetic_test"]
    review_status: Literal["reviewed"]
    pages: list[Page] = Field(min_length=1)


class Manifest(StrictModel):
    sources: list[Source] = Field(min_length=1)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def excerpts(text: str, page: Page) -> list[tuple[str, int, int, str]]:
    if page.table:
        rows = []
        normalized = " ".join(text.casefold().split())
        for row in page.table.rows:
            if len(row) != len(page.table.headers) or any(
                not cell.strip() or " ".join(cell.casefold().split()) not in normalized
                for cell in row
            ):
                raise ValueError("Tabla sin correspondencia verificable con la página")
            rows.append(
                (
                    "; ".join(f"{h}: {v}" for h, v in zip(page.table.headers, row, strict=True)),
                    0,
                    len(text),
                    "reviewed_table_rows",
                )
            )
        return rows
    start = text.index(page.start_marker) if page.start_marker else 0
    end = text.index(page.end_marker, start) if page.end_marker else len(text)
    if end <= start:
        raise ValueError("Selección vacía")
    tokens = list(re.finditer(r"\S+", text[start:end]))
    result = []
    for i in range(0, len(tokens), 140):
        left = start + tokens[i].start()
        right = start + tokens[min(i + 199, len(tokens) - 1)].end()
        result.append((text[left:right], left, right, "verbatim"))
        if i + 200 >= len(tokens):
            break
    return result


def build_catalogue(manifest_path: Path, output: Path) -> Catalogue:
    manifest = Manifest.model_validate_json(manifest_path.read_text())
    ids = [source.source_id for source in manifest.sources]
    if len(ids) != len(set(ids)):
        raise ValueError("source_id duplicado")
    config = {
        "manifest": manifest.model_dump(),
        "extractor": "pdfplumber-" + pdfplumber.__version__,
        "chunking": "lexical-200-overlap60-v1",
    }
    version = digest(json.dumps(config, sort_keys=True, ensure_ascii=False))
    evidence: list[Evidence] = []
    for source in manifest.sources:
        file = (manifest_path.parent / source.local_file).resolve()
        if not file.is_relative_to(manifest_path.parent.resolve()):
            raise ValueError("Archivo fuera de la raíz curada")
        if hashlib.sha256(file.read_bytes()).hexdigest() != source.sha256:
            raise ValueError("Hash distinto del manifiesto")
        try:
            with pdfplumber.open(file) as pdf:
                for page in source.pages:
                    if page.pdf_page > len(pdf.pages):
                        raise ValueError("Página inexistente")
                    text = pdf.pages[page.pdf_page - 1].extract_text() or ""
                    if len(text.strip()) < 20:
                        raise ValueError("Página sin texto utilizable; requiere revisión/OCR")
                    for fragment, start, end, transform in excerpts(text, page):
                        evidence.append(
                            Evidence(
                                evidence_id=digest(
                                    f"{version}:{source.source_id}:{page.pdf_page}:"
                                    f"{page.crop}:{start}:{end}:{fragment}"
                                ),
                                corpus_version=version,
                                source_id=source.source_id,
                                title=source.title,
                                edition=source.edition,
                                source_url=source.source_url,
                                pdf_page=page.pdf_page,
                                printed_page=page.printed_page,
                                section=page.section,
                                crop=page.crop,
                                text=fragment,
                                original_text=text,
                                start=start,
                                end=end,
                                transformation=transform,
                            )
                        )
        except (ValueError, IndexError) as exc:
            raise ValueError(f"Fuente {source.source_id}: {exc}") from exc
    if not evidence or len({e.evidence_id for e in evidence}) != len(evidence):
        raise ValueError("Catálogo vacío o evidencias duplicadas")
    catalogue = Catalogue(version, tuple(evidence))
    output.mkdir(parents=True, exist_ok=True)
    # Each activation is an immutable complete snapshot; no shared DB is mutated.
    with tempfile.TemporaryDirectory(dir=output) as temp:
        db_path = Path(temp) / "catalogue.sqlite"
        with closing(sqlite3.connect(db_path)) as db:
            with db:
                db.execute("CREATE TABLE evidence (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
                db.executemany(
                    "INSERT INTO evidence VALUES (?,?)",
                    [(e.evidence_id, json.dumps(asdict(e), ensure_ascii=False)) for e in evidence],
                )
                count = db.execute("SELECT count(*) FROM evidence").fetchone()[0]
                if count != len(evidence):
                    raise ValueError("Catálogo incompleto")
        target = output / f"{version}.sqlite"
        if target.exists():
            if read_snapshot(target, version) != catalogue:
                raise ValueError("Catálogo existente distinto del esperado")
        else:
            os.replace(db_path, target)
        pointer = Path(temp) / "active.json"
        pointer.write_text(
            json.dumps({"version": version, "count": count, "mode": "catalogue_preview"})
        )
        os.replace(pointer, output / "active.json")
    return catalogue


def read_snapshot(path: Path, version: str) -> Catalogue:
    try:
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
            items = tuple(
                Evidence(**json.loads(row[0]))
                for row in db.execute("SELECT payload FROM evidence ORDER BY rowid")
            )
        if not items or any(item.corpus_version != version for item in items):
            raise ValueError("Catálogo vacío o versión inconsistente")
        return Catalogue(version, items)
    except (sqlite3.Error, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Catálogo inválido") from exc


def load_catalogue(output: Path) -> Catalogue:
    active = json.loads((output / "active.json").read_text())
    version = active["version"]
    if not isinstance(version, str) or not re.fullmatch(r"[0-9a-f]{64}", version):
        raise ValueError("Versión inválida")
    catalogue = read_snapshot((output / f"{version}.sqlite").resolve(), version)
    if len(catalogue.evidence) != active["count"]:
        raise ValueError("Conteo inconsistente")
    return catalogue
