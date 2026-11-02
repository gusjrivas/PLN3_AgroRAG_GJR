# UI-06 - visibilidad del flujo de verificación

Fecha: 02/11/2026. Responsable y revisión: coordinador/frontend, misma sesión. Rama:
`fix/ui-show-verification-flow`. Propiedad: `src/agro_rag_ui/app.py`, `tests/ui/test_ui.py`,
`docs/frontend.md`, OpenSpec 05 y esta evidencia. No se realizaron llamadas a modelos ni servicios
pagos.

## Decisión de alcance

La solicitud pedía volver a mostrar una supuesta "votación de modelos". La inspección del contrato,
ADR-007, bootstrap y flujo de consulta confirmó que el producto usa un único adaptador de modelo
para dos roles secuenciales: investigador y verificador. El verificador emite `approve`, `revise`,
`clarify` o `abstain`; no agrega votos de modelos independientes. La UI muestra el mecanismo real,
la decisión y la cantidad de revisiones, sin introducir un contrato falso.

La consulta estructural usó el índice `PLN3_AgroRAG_GJR_security_review`. El índice estaba listo
pero desactualizado respecto de `main`; `check_index_coverage` marcó `metadata_changed` para código
y excluyó `docs/`. Por eso las afirmaciones materiales se verificaron además leyendo directamente
`src/agro_rag/application/query.py`, `src/agro_rag/bootstrap/app.py`, `src/agro_rag/api/schemas.py`,
`src/agro_rag_ui/app.py`, ADR-007 y la documentación de frontend.

## RED

Se agregó
`test_answer_shows_researcher_verifier_decision_without_claiming_model_vote`. El fixture devuelve
una respuesta aprobada con una revisión y exige investigador, verificador, decisión y revisión
visibles.

```text
uv run pytest tests/ui/test_ui.py::test_answer_shows_researcher_verifier_decision_without_claiming_model_vote -q
# exit 1: "investigador" no estaba en ningún elemento visible
```

## GREEN

`show_verification` traduce únicamente los valores cerrados del contrato público y presenta:
`Flujo de agentes: investigador -> verificador`, decisión y conteo singular/plural de revisiones.
Si la metadata falta o es inválida no inventa un estado.

```text
uv run pytest tests/ui/test_ui.py::test_answer_shows_researcher_verifier_decision_without_claiming_model_vote -q
# exit 0: 1 passed
```

## REFACTOR y regresión

```text
uv run pytest tests/ui/test_ui.py tests/ui/test_client.py -q
# exit 0: 17 passed

uv run ruff check src/agro_rag_ui/app.py tests/ui/test_ui.py
# exit 0

uv run mypy src/agro_rag_ui
# exit 0: 3 source files sin errores

uv run lint-imports
# exit 0: 2 contratos respetados

uv run pytest tests/ui tests/contract/test_query_api.py -q
# exit 0: 30 passed, 1 warning deprecada de Starlette/httpx

npx --yes @fission-ai/openspec@1.14.3 validate 05-frontend-hardening --strict
# exit 0: change valid

uv run ruff check .
git diff --check
# exit 0
```

El test usa un cliente API simulado y no es evidencia de calidad de un proveedor real. Commit de
implementación: `442e2e1` (`fix: show agent verification flow in UI`).
