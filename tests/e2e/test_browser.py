"""Real browser -> Streamlit -> FastAPI -> curated PDF. No LLM or paid services."""

import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest
from playwright.sync_api import expect, sync_playwright
from reportlab.pdfgen.canvas import Canvas

from agro_rag.infrastructure.corpus import build_catalogue

pytestmark = pytest.mark.e2e


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for(url, process):
    deadline = time.monotonic() + 30
    with httpx.Client(trust_env=False, timeout=0.5) as client:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise AssertionError("Server exited")
            try:
                if client.get(url).status_code == 200:
                    return
            except httpx.HTTPError:
                pass
            time.sleep(0.1)
    raise AssertionError("Server startup timeout")


def test_browser_searches_and_expands_real_pdf_evidence(tmp_path):
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
                        "source_id": "E2E",
                        "title": "Manual de prueba",
                        "authors": ["Test"],
                        "institution": "Test",
                        "edition": "2026",
                        "language": "es",
                        "source_url": "https://example.org/manual.pdf",
                        "access_date": "2026-10-22",
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
        )
    )
    catalogue = tmp_path / "catalogue"
    build_catalogue(manifest, catalogue)
    backend_port = free_port()
    ui_port = free_port()
    assert backend_port != ui_port
    env = dict(
        os.environ,
        AGRO_READER_KEY="test-e2e-key-123456789",
        AGRO_CATALOGUE_PATH=str(catalogue),
        AGRO_MODEL="",
        AGRO_API_URL=f"http://127.0.0.1:{backend_port}",
    )
    root = Path(__file__).resolve().parents[2]
    processes = []
    with (tmp_path / "servers.log").open("w") as log:
        try:
            backend = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "agro_rag.bootstrap.app:create_app",
                    "--factory",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(backend_port),
                ],
                cwd=root,
                env=env,
                stdout=log,
                stderr=log,
            )
            processes.append(backend)
            wait_for(f"http://127.0.0.1:{backend_port}/health/live", backend)
            ui = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "streamlit",
                    "run",
                    "src/agro_rag_ui/app.py",
                    "--server.address",
                    "127.0.0.1",
                    "--server.port",
                    str(ui_port),
                    "--server.headless",
                    "true",
                    "--browser.gatherUsageStats",
                    "false",
                ],
                cwd=root,
                env=env,
                stdout=log,
                stderr=log,
            )
            processes.append(ui)
            wait_for(f"http://127.0.0.1:{ui_port}/_stcore/health", ui)
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                page = browser.new_page()
                page.goto(f"http://127.0.0.1:{ui_port}")
                page.get_by_role("textbox", name="¿Qué querés saber?").fill("humedad lechuga")
                page.get_by_role("button", name="Consultar", exact=True).click()
                page.get_by_text("Manual de prueba", exact=True).click()
                expect(
                    page.get_by_text(
                        "Lechuga: conservar humedad constante durante el crecimiento.", exact=True
                    )
                ).to_be_visible()
                expect(
                    page.get_by_text("Página PDF 1 · página impresa 7", exact=False)
                ).to_be_visible()
                page.screenshot(path=str(tmp_path / "preview.png"), full_page=True)
                browser.close()
        finally:
            for process in reversed(processes):
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
