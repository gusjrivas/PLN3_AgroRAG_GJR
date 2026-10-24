# Evidencia TDD: caché observable de retrieval

Fecha: 24/10/2026. Responsable y revisor disponible: misma sesión Codex; revisión humana pendiente.
Rama: `feat/05-retrieval-cache`. Base lógica: `main` más el hardening del PR #10 que había quedado
fusionado sólo en la rama intermedia de #9.

## Alcance y propiedad

Implementar `OPS-01-hit` y `OPS-01-invalidate` sin cachear generación ni errores. Archivos de código
propios del corte:

- `src/agro_rag/application/query.py`
- `tests/unit/test_query.py`

La instancia de `QueryService` fija retriever/configuración. La clave observable usa versión de
corpus, pregunta normalizada y cultivo. No hay red, modelo real ni servicios pagos en estas pruebas.

## RED

Comando:

```text
.venv\Scripts\python.exe -m pytest -q tests\unit\test_query.py::test_ops_01_retrieval_cache_hit_is_normalized_and_observable tests\unit\test_query.py::test_ops_01_retrieval_cache_invalidates_on_filter_and_version tests\unit\test_query.py::test_ops_01_retrieval_errors_are_never_cached
```

Resultado: exit code 1, `2 failed, 1 passed`. La invalidación pasaba porque cada llamada era un miss;
fallaron el hit normalizado y el reuso posterior a la recuperación de un proveedor transitorio.

## GREEN

Cambio mínimo: LRU de 128 entradas por defecto, clave `(corpus_version, normalized_question, crop)`,
promoción LRU al leer, expulsión del más antiguo y escritura sólo después de una búsqueda exitosa.

Mismo comando: exit code 0, `3 passed in 0.04s`.

## REFACTOR y cierre

Resultados locales finales:

- `.venv\Scripts\python.exe -m pytest -q`: exit 0, `131 passed, 2 deselected`.
- `.venv\Scripts\ruff.exe check .`: exit 0.
- `.venv\Scripts\ruff.exe format --check .`: exit 0, 124 archivos formateados.
- `.venv\Scripts\mypy.exe src`: exit 0, 27 archivos sin errores.
- `.venv\Scripts\lint-imports.exe`: exit 0, 2 contratos mantenidos.
- `npx --yes @fission-ai/openspec@latest validate 05-frontend-hardening --strict`: exit 0.

La revisión del impacto fue realizada por la misma sesión. El grafo identificó `QueryService`, su
bootstrap y pruebas como consumidores directos; los documentos excluidos del índice se revisaron
desde el diff. Pendiente añadir commit, PR y CI remota.

## Límites

- El cache es local al proceso y no pretende coordinación distribuida.
- Dos misses concurrentes de una clave pueden ejecutar dos búsquedas; el resultado final sigue
  siendo correcto. Evitar stampede queda fuera del POC mientras haya sólo dos consultas activas.
- `OPS-01-redaccion` continúa abierto hasta implementar el sink de auditoría estructurado.
