# Evidencia TDD: frontera async de retrieval

Fecha: 24/10/2026. Responsable y revisor disponible: misma sesión Codex; revisión humana pendiente.
Rama: `feat/03-retrieval-api-activation`. Base: `feat/03-retrieval-live-eval` (PR #9 hacia `main`).

## Alcance y propiedad

Preparar la frontera operacional necesaria para una futura activación semántica sin cambiar el
modo público BM25. Archivos de código propios del corte:

- `src/agro_rag/application/query.py`
- `src/agro_rag/api/query.py`
- `tests/unit/test_query.py`
- `tests/contract/test_query_api.py`

La llamada síncrona de retrieval debe ejecutarse en un worker, consumir el mismo deadline global y
producir errores HTTP tipados y redactados. No se cargan modelos ni se llama a Pinecone en pruebas.

## RED

Comando:

```text
.venv\Scripts\python.exe -m pytest -q tests\unit\test_query.py::test_retrieval_runs_outside_the_event_loop_thread tests\unit\test_query.py::test_deadline_covers_blocking_retrieval tests\contract\test_query_api.py::test_retrieval_failure_is_503_and_redacted
```

Resultado: exit code 1, `3 failed`. Fallos observados:

- retrieval ejecutó en el mismo thread que el event loop;
- un `sleep` síncrono superó el deadline sin lanzar `TimeoutError`;
- `RetrievalUnavailable` produjo HTTP 500 en vez de 503.

## GREEN

Cambio mínimo: `asyncio.to_thread` alrededor del puerto síncrono y traducción explícita de
`RetrievalUnavailable`/`RetrievalContractError` en la capa API.

Mismo comando: exit code 0, `3 passed in 0.73s`.

## REFACTOR y cierre

Resultados locales:

- `.venv\Scripts\python.exe -m pytest -q`: exit 0, `128 passed, 2 deselected`.
- `.venv\Scripts\ruff.exe check .`: exit 0.
- `.venv\Scripts\ruff.exe format --check .`: exit 0, 123 archivos formateados.
- `.venv\Scripts\mypy.exe src`: exit 0, 27 archivos sin errores.
- `.venv\Scripts\lint-imports.exe`: exit 0, 2 contratos mantenidos.
- `npx --yes @fission-ai/openspec@latest validate 03-retrieval --strict`: exit 0.

La revisión fue realizada por la misma sesión. Commit funcional: `180d19b`. PR apilado sobre #9:
[#10](https://github.com/gusjrivas/PLN3_AgroRAG_GJR/pull/10). CI inicial del commit funcional:
`specs`, `offline` y `browser` aprobados.

## Riesgos restantes

- Cancelar el await al vencer el deadline no detiene por la fuerza una operación ya iniciada en el
  SDK; limita la respuesta HTTP y libera el event loop. El timeout propio del proveedor sigue siendo
  obligatorio.
- Este corte no activa Pinecone/hybrid/reranker ni resuelve el tokenizer exacto del modelo final.
