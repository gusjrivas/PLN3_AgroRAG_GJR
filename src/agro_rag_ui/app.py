from typing import Any

import streamlit as st
from pydantic_settings import BaseSettings, SettingsConfigDict

from agro_rag_ui.client import ApiClient, ApiError


class UISettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AGRO_", env_file=".env", extra="ignore")
    reader_key: str = ""
    api_url: str = "http://127.0.0.1:8000"


def clear_result_state() -> None:
    for key in (
        "result",
        "api_error",
        "submitted_query",
        "submitted_crop",
        "submitted_context",
        "clarification_answers",
    ):
        st.session_state.pop(key, None)


def show_evidence(items: list[dict[str, Any]]) -> None:
    for item in items:
        with st.expander(item["title"]):
            st.caption(
                f"Página PDF {item['pdf_page']} · página impresa {item['printed_page']}"
                f" · {item.get('edition', '')}"
            )
            st.text(item.get("excerpt", item.get("text", "")))
            st.link_button("Abrir documento fuente", item["source_url"])


def main() -> None:
    st.set_page_config(page_title="AgroRAG", page_icon="🌱", layout="centered")
    st.title("AgroRAG")
    st.caption("Riego de tomate y lechuga · documentación de INTA y FAO")
    config = UISettings()
    if not config.reader_key:
        st.warning("Configurá la clave de lectura para conectar con el servicio.")
        st.stop()
    client = ApiClient(config.api_url, config.reader_key)
    mode = st.sidebar.radio(
        "Cómo consultar",
        ["Explorar fuentes", "Respuesta verificada"],
        on_change=clear_result_state,
    )
    st.sidebar.caption("Corpus piloto: consultar la edición y las condiciones de cada fuente.")
    if mode == "Explorar fuentes":
        st.info(
            "Explorá fragmentos de los documentos disponibles. "
            "Este modo no genera una respuesta redactada."
        )
    else:
        st.info(
            "Generá una respuesta con citas y verificación automática. "
            "Este modo requiere que el servicio tenga un modelo configurado."
        )
    st.caption(
        "1. Elegí el modo. 2. Escribí la pregunta y, si corresponde, el contexto. "
        "3. Presioná Consultar."
    )
    form_version = st.session_state.get("query_form_version", 0)
    with st.form(f"query-{form_version}"):
        question = st.text_area(
            "¿Qué querés saber?",
            max_chars=2000,
            placeholder="¿Cuándo es crítico evitar la falta de agua en tomate?",
            key=f"question-{form_version}",
        )
        crop_name = st.selectbox(
            "Cultivo",
            ["Sin especificar", "Tomate", "Lechuga"],
            key=f"crop-{form_version}",
        )
        stage = st.text_input(
            "Etapa del cultivo (opcional)", max_chars=500, key=f"stage-{form_version}"
        )
        soil = st.text_input(
            "Descripción del suelo (opcional)", max_chars=500, key=f"soil-{form_version}"
        )
        submitted = st.form_submit_button("Consultar", type="primary")
    if submitted:
        st.session_state.pop("result", None)
        st.session_state.pop("api_error", None)
        if not question.strip():
            st.session_state.api_error = "Escribí una pregunta antes de consultar."
        else:
            crop = {"Tomate": "tomato", "Lechuga": "lettuce"}.get(crop_name)
            context = {
                k: v for k, v in {"growth_stage": stage, "soil_description": soil}.items() if v
            }
            try:
                with st.spinner("Consultando las fuentes…"):
                    result = (
                        client.search(question, crop)
                        if mode == "Explorar fuentes"
                        else (client.query(question, crop, context))
                    )
                st.session_state.result = result
                st.session_state.submitted_query = question
                st.session_state.submitted_crop = crop
                st.session_state.submitted_context = context
                st.session_state.clarification_answers = []
            except ApiError as exc:
                st.session_state.api_error = str(exc)
    if "api_error" in st.session_state:
        st.error(st.session_state.api_error)
    if "result" not in st.session_state:
        return
    result = st.session_state.result
    st.caption(f"Resultado para: “{st.session_state.submitted_query}”")
    if result.get("mode") == "lexical_preview":
        st.info("Fragmentos recuperados de las fuentes. Este modo no genera una respuesta.")
        if not result.get("evidence"):
            st.warning("No se encontraron fragmentos para esa consulta.")
        show_evidence(result.get("evidence", []))
    else:
        status = result.get("status")
        if status == "answered":
            st.subheader("Respuesta verificada automáticamente")
            st.text(result["answer"])
        elif status == "needs_clarification":
            st.info("Falta contexto para responder:")
            for value in result.get("missing_information", []):
                st.text(value)
            previous = st.session_state.get("clarification_answers", [])
            if len(previous) < 3:
                with st.form("clarification"):
                    extra = st.text_area("Completá el contexto solicitado", max_chars=500)
                    clarify = st.form_submit_button("Enviar aclaración")
                if clarify and extra.strip():
                    answers = [*previous, extra.strip()]
                    try:
                        with st.spinner("Revisando con el contexto adicional…"):
                            st.session_state.result = client.query(
                                st.session_state.submitted_query,
                                st.session_state.submitted_crop,
                                st.session_state.submitted_context,
                                {
                                    "original_question": st.session_state.submitted_query,
                                    "answers": answers,
                                },
                            )
                        st.session_state.clarification_answers = answers
                        st.rerun()
                    except ApiError as exc:
                        st.error(str(exc))
            else:
                st.info("Reformulá la consulta incluyendo el contexto reunido.")
        else:
            st.warning("No hay evidencia suficiente para una respuesta verificada.")
        show_evidence(result.get("citations", []))
        for limit in result.get("limitations", []):
            st.caption(limit)
    if st.button("Nueva consulta"):
        clear_result_state()
        st.session_state.query_form_version = form_version + 1
        st.rerun()


if __name__ == "__main__":
    main()
