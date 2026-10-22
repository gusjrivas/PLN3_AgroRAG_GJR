from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_preview_shows_provenance_without_duplicate_request(monkeypatch):
    from agro_rag_ui.client import ApiClient

    calls = []

    def search(self, question, crop):
        calls.append(question)
        return {
            "mode": "lexical_preview",
            "evidence": [
                {
                    "text": "Humedad constante.",
                    "title": "Manual INTA",
                    "pdf_page": 72,
                    "printed_page": "70",
                    "source_url": "https://example.org/doc.pdf",
                }
            ],
        }

    monkeypatch.setattr(ApiClient, "search", search)
    monkeypatch.setenv("AGRO_READER_KEY", "test-reader-token-123456")
    app = AppTest.from_file(str(Path("src/agro_rag_ui/app.py").resolve())).run()
    app.text_area[0].set_value("¿Cómo regar la lechuga?")
    app.button[0].click().run()
    assert not app.exception
    assert any("Humedad constante" in t.value for t in app.text)
    assert any("72" in c.value and "70" in c.value for c in app.caption)
    app.run()
    assert len(calls) == 1


def test_missing_key_does_not_send_request(monkeypatch):
    monkeypatch.delenv("AGRO_READER_KEY", raising=False)
    app = AppTest.from_file(str(Path("src/agro_rag_ui/app.py").resolve())).run()
    assert not app.exception
    assert len(app.warning) == 1


def test_http_failure_is_visible_and_not_an_answer(monkeypatch):
    from agro_rag_ui.client import ApiClient, ApiError

    monkeypatch.setenv("AGRO_READER_KEY", "test-reader-token-123456")

    def fail(*args):
        raise ApiError("Servicio no disponible (503).")

    monkeypatch.setattr(ApiClient, "search", fail)
    app = AppTest.from_file(str(Path("src/agro_rag_ui/app.py").resolve())).run()
    app.text_area[0].set_value("riego")
    app.button[0].click().run()
    assert not app.exception
    assert "503" in app.error[0].value


def test_clarification_keeps_original_question(monkeypatch):
    from agro_rag_ui.client import ApiClient

    monkeypatch.setenv("AGRO_READER_KEY", "test-reader-token-123456")
    calls = []

    def query(self, question, crop, context, clarification=None):
        calls.append((question, clarification))
        return {
            "status": "needs_clarification",
            "missing_information": ["¿Qué etapa?"],
            "citations": [],
            "limitations": [],
        }

    monkeypatch.setattr(ApiClient, "query", query)
    app = AppTest.from_file(str(Path("src/agro_rag_ui/app.py").resolve())).run()
    app.sidebar.radio[0].set_value("Respuesta verificada").run()
    app.text_area[0].set_value("¿Cuánto riego?")
    app.button[0].click().run()
    assert len(app.text_area) == 2
    app.text_area[1].set_value("Cuajado de frutos")
    app.button[1].click().run()
    assert calls[1][0] == "¿Cuánto riego?"
    assert calls[1][1]["answers"] == ["Cuajado de frutos"]
