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


def test_semantic_preview_is_rendered_as_evidence_not_as_generated_answer(monkeypatch):
    from agro_rag_ui.client import ApiClient

    def search(self, question, crop):
        return {
            "mode": "hybrid_preview",
            "evidence": [
                {
                    "text": "Evidencia semántica trazable.",
                    "title": "Manual INTA",
                    "pdf_page": 4,
                    "printed_page": "2",
                    "source_url": "https://example.org/doc.pdf",
                }
            ],
        }

    monkeypatch.setattr(ApiClient, "search", search)
    monkeypatch.setenv("AGRO_READER_KEY", "test-reader-token-123456")
    app = AppTest.from_file(str(Path("src/agro_rag_ui/app.py").resolve())).run()
    app.text_area[0].set_value("riego tomate")
    app.button[0].click().run()

    assert not app.exception
    assert any("Evidencia semántica trazable" in value.value for value in app.text)
    assert any("no genera una respuesta" in value.value.lower() for value in app.info)


def test_preview_explains_mode_and_allows_a_second_query(monkeypatch):
    from agro_rag_ui.client import ApiClient

    calls = []

    def search(self, question, crop):
        calls.append(question)
        return {
            "mode": "lexical_preview",
            "evidence": [
                {
                    "text": f"Resultado para {question}",
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

    assert any("no genera una respuesta" in value.value.lower() for value in app.info)
    app.text_area[0].set_value("primera consulta")
    app.button[0].click().run()
    next(button for button in app.button if button.label == "Nueva consulta").click().run()
    app.text_area[0].set_value("segunda consulta")
    next(button for button in app.button if button.label == "Consultar").click().run()

    assert calls == ["primera consulta", "segunda consulta"]
    assert any("segunda consulta" in value.value for value in app.caption)
    assert any("Resultado para segunda consulta" in value.value for value in app.text)
    assert not any("Resultado para primera consulta" in value.value for value in app.text)


def test_new_query_clears_result_without_calling_api_again(monkeypatch):
    from agro_rag_ui.client import ApiClient

    calls = []

    def search(self, question, crop):
        calls.append(question)
        return {"mode": "lexical_preview", "evidence": []}

    monkeypatch.setattr(ApiClient, "search", search)
    monkeypatch.setenv("AGRO_READER_KEY", "test-reader-token-123456")
    app = AppTest.from_file(str(Path("src/agro_rag_ui/app.py").resolve())).run()
    app.text_area[0].set_value("riego")
    app.button[0].click().run()

    new_query = next(button for button in app.button if button.label == "Nueva consulta")
    new_query.click().run()

    assert calls == ["riego"]
    assert not any("Fragmentos recuperados" in value.value for value in app.info)
    assert app.text_area[0].value == ""


def test_result_hides_query_form_until_new_query(monkeypatch):
    from agro_rag_ui.client import ApiClient

    monkeypatch.setenv("AGRO_READER_KEY", "test-reader-token-123456")
    monkeypatch.setattr(
        ApiClient,
        "search",
        lambda self, question, crop: {"mode": "lexical_preview", "evidence": []},
    )
    app = AppTest.from_file(str(Path("src/agro_rag_ui/app.py").resolve())).run()
    app.text_area[0].set_value("riego")
    next(button for button in app.button if button.label == "Consultar").click().run()

    assert not any(button.label == "Consultar" for button in app.button)
    assert not any(area.label == "¿Qué querés saber?" for area in app.text_area)

    next(button for button in app.button if button.label == "Nueva consulta").click().run()

    assert any(button.label == "Consultar" for button in app.button)
    assert next(area for area in app.text_area if area.label == "¿Qué querés saber?").value == ""


def test_changing_mode_clears_the_previous_result(monkeypatch):
    from agro_rag_ui.client import ApiClient

    calls = []

    def search(self, question, crop):
        calls.append(question)
        return {"mode": "lexical_preview", "evidence": []}

    monkeypatch.setattr(ApiClient, "search", search)
    monkeypatch.setenv("AGRO_READER_KEY", "test-reader-token-123456")
    app = AppTest.from_file(str(Path("src/agro_rag_ui/app.py").resolve())).run()
    app.text_area[0].set_value("riego")
    app.button[0].click().run()

    app.sidebar.radio[0].set_value("Respuesta verificada").run()

    assert calls == ["riego"]
    assert not any("Fragmentos recuperados" in value.value for value in app.info)
    assert not any("Resultado para:" in value.value for value in app.caption)


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
    assert len(app.text_area) == 1
    next(
        area for area in app.text_area if area.label == "Completá el contexto solicitado"
    ).set_value("Cuajado de frutos")
    next(button for button in app.button if button.label == "Enviar aclaración").click().run()
    assert calls[1][0] == "¿Cuánto riego?"
    assert calls[1][1]["answers"] == ["Cuajado de frutos"]


def test_verified_answer_is_prominent_and_identifies_openai(monkeypatch):
    from agro_rag_ui.client import ApiClient

    monkeypatch.setenv("AGRO_READER_KEY", "test-reader-token-123456")

    def query(self, question, crop, context, clarification=None):
        return {
            "status": "answered",
            "answer": "Evitá el déficit durante el cuajado de frutos.",
            "citations": [],
            "limitations": [],
        }

    monkeypatch.setattr(ApiClient, "query", query)
    app = AppTest.from_file(str(Path("src/agro_rag_ui/app.py").resolve())).run()
    app.sidebar.radio[0].set_value("Respuesta verificada").run()
    app.text_area[0].set_value("¿Cuándo es crítico el riego del tomate?")
    app.button[0].click().run()

    assert any("OpenAI" in message.value for message in app.success)
    assert any("cuajado de frutos" in text.value for text in app.text)
