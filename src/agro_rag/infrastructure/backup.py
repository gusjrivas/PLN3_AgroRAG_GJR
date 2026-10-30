"""Validated catalogue backup/restore with atomic activation."""

import hashlib
import json
import os
import re
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from agro_rag.domain.evidence import Catalogue
from agro_rag.infrastructure.corpus import load_catalogue, read_snapshot


@dataclass(frozen=True)
class BackupMetadata:
    corpus_version: str
    evidence_count: int
    release: str
    commit: str
    image: str
    files: dict[str, str]


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _metadata(payload: bytes) -> BackupMetadata:
    try:
        value = json.loads(payload)
        metadata = BackupMetadata(
            corpus_version=value["corpus_version"],
            evidence_count=value["evidence_count"],
            release=value["release"],
            commit=value["commit"],
            image=value["image"],
            files=value["files"],
        )
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Metadata de backup inválida") from exc
    snapshot = f"{metadata.corpus_version}.sqlite"
    if (
        not re.fullmatch(r"[0-9a-f]{64}", metadata.corpus_version)
        or not isinstance(metadata.evidence_count, int)
        or metadata.evidence_count < 1
        or not isinstance(metadata.release, str)
        or not metadata.release
        or not isinstance(metadata.commit, str)
        or not metadata.commit
        or not isinstance(metadata.image, str)
        or not metadata.image
        or not isinstance(metadata.files, dict)
        or set(metadata.files) != {"active.json", snapshot}
        or any(not re.fullmatch(r"[0-9a-f]{64}", digest) for digest in metadata.files.values())
    ):
        raise ValueError("Metadata de backup inválida")
    return metadata


def backup_catalogue(
    catalogue_path: Path,
    destination: Path,
    *,
    release: str,
    commit: str,
    image: str,
) -> BackupMetadata:
    catalogue = load_catalogue(catalogue_path)
    active_path = catalogue_path / "active.json"
    snapshot_name = f"{catalogue.version}.sqlite"
    snapshot_path = catalogue_path / snapshot_name
    active = active_path.read_bytes()
    snapshot = snapshot_path.read_bytes()
    metadata = BackupMetadata(
        corpus_version=catalogue.version,
        evidence_count=len(catalogue.evidence),
        release=release,
        commit=commit,
        image=image,
        files={"active.json": _sha256(active), snapshot_name: _sha256(snapshot)},
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=destination.parent, suffix=".zip")
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("backup.json", json.dumps(metadata.__dict__, sort_keys=True))
            archive.writestr("active.json", active)
            archive.writestr(snapshot_name, snapshot)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return metadata


def restore_catalogue(archive_path: Path, catalogue_path: Path) -> Catalogue:
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or "backup.json" not in names:
            raise ValueError("Contenido de backup inválido")
        metadata = _metadata(archive.read("backup.json"))
        snapshot_name = f"{metadata.corpus_version}.sqlite"
        if set(names) != {"backup.json", "active.json", snapshot_name}:
            raise ValueError("Contenido de backup inválido")
        active = archive.read("active.json")
        snapshot = archive.read(snapshot_name)

    if (
        _sha256(active) != metadata.files["active.json"]
        or _sha256(snapshot) != metadata.files[snapshot_name]
    ):
        raise ValueError("Fallo de integridad del backup")
    try:
        pointer = json.loads(active)
    except json.JSONDecodeError as exc:
        raise ValueError("Manifiesto activo inválido") from exc
    if (
        pointer.get("version") != metadata.corpus_version
        or pointer.get("count") != metadata.evidence_count
    ):
        raise ValueError("Manifiesto activo inconsistente")

    catalogue_path.mkdir(parents=True, exist_ok=True)
    snapshot_path = catalogue_path / snapshot_name
    if snapshot_path.exists():
        if _sha256(snapshot_path.read_bytes()) != metadata.files[snapshot_name]:
            raise ValueError("Snapshot existente distinto del backup")
    else:
        descriptor, temporary_name = tempfile.mkstemp(dir=catalogue_path, suffix=".sqlite")
        os.close(descriptor)
        temporary = Path(temporary_name)
        try:
            temporary.write_bytes(snapshot)
            os.replace(temporary, snapshot_path)
        finally:
            temporary.unlink(missing_ok=True)

    restored = read_snapshot(snapshot_path, metadata.corpus_version)
    if len(restored.evidence) != metadata.evidence_count:
        raise ValueError("Conteo restaurado inconsistente")
    descriptor, temporary_name = tempfile.mkstemp(dir=catalogue_path, suffix=".json")
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        temporary.write_bytes(active)
        os.replace(temporary, catalogue_path / "active.json")
    finally:
        temporary.unlink(missing_ok=True)
    return restored
