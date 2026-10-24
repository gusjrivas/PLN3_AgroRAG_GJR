"""Offline validation for the reproducible DEL-01 delivery package."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

_REQUIRED_PATHS = (
    ".env.example",
    "uv.lock",
    "data/manifest.json",
    "docs/run-local.md",
    "docs/report.md",
    "docs/demo.md",
    "scripts/build_report.py",
    "output/pdf/agro-rag-report.pdf",
)
_COMMANDS = (
    "uv sync --frozen",
    "uv run agro-rag download",
    "uv run agro-rag ingest",
    "uv run uvicorn",
    "uv run streamlit",
    "uv run pytest",
)
_REPORT_SECTIONS = (
    "Objetivo, problema y alcance",
    "Corpus y procedencia",
    "Arquitectura",
    "Implementación y reutilización",
    "Metodología de evaluación",
    "Resultados y evidencia",
    "Conclusiones",
    "Declaración de asistencia de IA",
)
_DEMO_MARKERS = ("00:00", "02:00", "05:00", "09:00", "13:00", "15:00")


@dataclass(frozen=True)
class ArtifactDigest:
    path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class DeliveryValidation:
    artifacts: tuple[ArtifactDigest, ...]
    commands: tuple[str, ...]

    @property
    def artifact_count(self) -> int:
        return len(self.artifacts)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"No se pudo leer el artefacto: {path.name}") from exc


def validate_delivery(root: Path) -> DeliveryValidation:
    """Validate the tracked package without network access or secret values."""
    root = root.resolve()
    paths = tuple(root / relative for relative in _REQUIRED_PATHS)
    missing = tuple(
        relative
        for relative, path in zip(_REQUIRED_PATHS, paths, strict=True)
        if not path.is_file()
    )
    if missing:
        raise ValueError(f"Artefactos faltantes: {', '.join(missing)}")

    runbook = _read_text(root / "docs/run-local.md")
    report = _read_text(root / "docs/report.md")
    demo = _read_text(root / "docs/demo.md")
    checked_text = "\n".join((report, demo))
    if re.search(r"\b(?:TODO|TBD|PLACEHOLDER)\b", checked_text, flags=re.IGNORECASE):
        raise ValueError("La entrega contiene un placeholder no resuelto")
    if any(command not in runbook for command in _COMMANDS):
        raise ValueError("El runbook no contiene todos los comandos reproducibles")
    if any(section not in report for section in _REPORT_SECTIONS):
        raise ValueError("El informe no contiene todas las secciones requeridas")
    if any(marker not in demo for marker in _DEMO_MARKERS):
        raise ValueError("El guion no cubre los 15 minutos de la demo")
    if "pending_human" not in report or "benchmark de 60 casos" not in report:
        raise ValueError("El informe oculta una limitación científica abierta")
    if not (root / "output/pdf/agro-rag-report.pdf").read_bytes().startswith(b"%PDF-"):
        raise ValueError("El informe final no es un PDF válido")

    artifacts = tuple(
        ArtifactDigest(
            path=relative,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            size_bytes=path.stat().st_size,
        )
        for relative, path in zip(_REQUIRED_PATHS, paths, strict=True)
    )
    return DeliveryValidation(artifacts=artifacts, commands=_COMMANDS)
