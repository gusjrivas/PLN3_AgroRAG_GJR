"""Opt-in browser characterization of the released API/UI images under Compose."""

import hashlib
import json
import os
import socket
import subprocess
import time
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from playwright.sync_api import expect, sync_playwright
from reportlab.pdfgen.canvas import Canvas

pytestmark = pytest.mark.e2e
ROOT = Path(__file__).resolve().parents[2]


def _port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _run(
    command: list[str], *, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return completed


def _wait(url: str, timeout: float = 60) -> None:
    deadline = time.monotonic() + timeout
    with httpx.Client(trust_env=False, timeout=1) as client:
        while time.monotonic() < deadline:
            try:
                if client.get(url).status_code == 200:
                    return
            except httpx.HTTPError:
                pass
            time.sleep(0.25)
    raise AssertionError(f"Timeout esperando {url}")


def _fixture(tmp_path: Path) -> Path:
    document = tmp_path / "manual.pdf"
    pdf = Canvas(str(document))
    pdf.drawString(50, 750, "Lechuga: conservar humedad constante durante el crecimiento.")
    pdf.showPage()
    pdf.save()
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "source_id": "COMPOSE-E2E",
                        "title": "Manual Compose",
                        "authors": ["Test"],
                        "institution": "Test",
                        "edition": "2026",
                        "language": "es",
                        "source_url": "https://example.org/manual.pdf",
                        "access_date": "2026-10-30",
                        "local_file": "manual.pdf",
                        "sha256": hashlib.sha256(document.read_bytes()).hexdigest(),
                        "rights_status": "synthetic_test",
                        "review_status": "reviewed",
                        "pages": [
                            {
                                "pdf_page": 1,
                                "printed_page": "7",
                                "section": "Riego",
                                "crop": "lettuce",
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return manifest


def test_compose_browser_flow_survives_restart(tmp_path: Path) -> None:
    api_image = os.getenv("AGRO_E2E_API_IMAGE")
    ui_image = os.getenv("AGRO_E2E_UI_IMAGE")
    if not api_image or not ui_image:
        pytest.skip("Defina AGRO_E2E_API_IMAGE y AGRO_E2E_UI_IMAGE para el E2E Compose")

    manifest = _fixture(tmp_path)
    suffix = uuid4().hex[:10]
    project = f"agrorag-e2e-{suffix}"
    volume = f"agrorag_catalogue_e2e_{suffix}"
    api_port, ui_port = _port(), _port()
    reader_key = "compose-e2e-reader-key"
    env = {
        **os.environ,
        "AGRO_API_IMAGE": api_image,
        "AGRO_UI_IMAGE": ui_image,
        "AGRO_CATALOGUE_VOLUME": volume,
        "AGRO_READER_KEY": reader_key,
        "AGRO_API_PORT": str(api_port),
        "AGRO_UI_PORT": str(ui_port),
    }
    compose = [
        "docker",
        "compose",
        "-p",
        project,
        "-f",
        "compose.yaml",
        "-f",
        "compose.dev.yaml",
    ]

    _run(["docker", "volume", "create", volume])
    try:
        _run(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--mount",
                f"type=bind,source={manifest.parent},target=/fixture,readonly",
                "--mount",
                f"type=volume,source={volume},target=/var/lib/agrorag/catalogue",
                api_image,
                "agro-rag",
                "ingest",
                "/fixture/manifest.json",
                "--output",
                "/var/lib/agrorag/catalogue",
            ]
        )
        _run([*compose, "up", "-d", "--wait", "--no-build", "api", "ui"], env=env)
        _wait(f"http://127.0.0.1:{ui_port}/_stcore/health")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            page.goto(f"http://127.0.0.1:{ui_port}")
            page.locator("textarea").fill("humedad lechuga")
            page.get_by_role("button", name="Consultar", exact=True).click()
            page.get_by_text("Manual Compose", exact=True).click()
            expect(
                page.get_by_text(
                    "Lechuga: conservar humedad constante durante el crecimiento.", exact=True
                )
            ).to_be_visible()

            _run([*compose, "restart", "api", "ui"], env=env)
            _wait(f"http://127.0.0.1:{ui_port}/_stcore/health")
            corpus = httpx.get(
                f"http://127.0.0.1:{api_port}/v1/corpus",
                headers={"X-API-Key": reader_key},
                trust_env=False,
            )
            assert corpus.status_code == 200
            assert corpus.json()["evidence_count"] == 1
            page.goto(f"http://127.0.0.1:{ui_port}")
            expect(page.get_by_text("AgroRAG", exact=True)).to_be_visible()
            browser.close()
    finally:
        subprocess.run([*compose, "down"], cwd=ROOT, env=env, check=False, capture_output=True)
        inspected = subprocess.run(
            ["docker", "volume", "inspect", volume, "--format", "{{.Name}}"],
            check=False,
            capture_output=True,
            text=True,
        )
        if inspected.returncode == 0 and inspected.stdout.strip() == volume:
            _run(["docker", "volume", "rm", volume])
