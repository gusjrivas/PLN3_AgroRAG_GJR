"""Explicit administrative downloads of curated institutional PDFs."""

import hashlib
import os
import tempfile
from pathlib import Path

import httpx

ALLOWED_HOSTS = {"www.argentina.gob.ar", "www.wcc.nrcs.usda.gov"}


def download_file(url: str, target: Path, expected: str, client: httpx.Client) -> None:
    parsed = httpx.URL(url)
    if parsed.scheme != "https" or parsed.host not in ALLOWED_HOSTS:
        raise ValueError("Fuente fuera de la lista institucional permitida")
    if target.exists():
        if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            raise ValueError("Archivo existente con hash distinto; no se reemplaza")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as temp:
        pending = Path(temp) / "download.pdf"
        sha = hashlib.sha256()
        size = 0
        with (
            client.stream("GET", url, follow_redirects=False) as response,
            pending.open("wb") as file,
        ):
            response.raise_for_status()
            for block in response.iter_bytes():
                size += len(block)
                if size > 50_000_000:
                    raise ValueError("PDF supera 50 MB")
                sha.update(block)
                file.write(block)
        with pending.open("rb") as file:
            if file.read(5) != b"%PDF-" or sha.hexdigest() != expected:
                raise ValueError("Contenido o hash de PDF inválido")
        os.replace(pending, target)
