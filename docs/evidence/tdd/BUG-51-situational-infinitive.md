# BUG-51 — aclaración situacional con infinitivo

Fecha: 2026-11-10. Issue: #51. Rama: `fix/situational-query-infinitives`.
Base: `701d313ae2951d634c7409e4b75abbf6fb0227e1`.
Propiedad: `src/agro_rag/application/query.py`, pruebas de consulta y esta evidencia.

## Hallazgo reproducido

La consulta real `Hace mucho calor, ¿debería cambiar el riego?`, sin cultivo, etapa, región ni
descripción del suelo, llegó al investigador OpenAI y terminó como `answered`. El preflight
reconocía la forma `cambio`, pero no la construcción `debería cambiar` normalizada como
`deberia cambiar`.

## RED

Se agregó primero el texto exacto informado por el usuario al escenario unitario que exige
`needs_clarification` sin invocar el modelo:

```text
python -m pytest tests/unit/test_query.py::test_context_dependent_decisions_request_clarification_without_model -q -p no:cacheprovider --basetemp .tmp-bug51-red
# exit 1: 1 failed, 6 passed
# fallo esperado: FakeModel fue invocado como researcher y agotó sus resultados
```

Luego se fijó el mismo límite en el contrato HTTP con un modelo que falla si recibe una llamada:

```text
python -m pytest tests/contract/test_query_api.py::test_situational_irrigation_infinitive_clarifies_without_model_call -q -p no:cacheprovider --basetemp .tmp-bug51-contract-red
# exit 1: el modelo prohibido fue invocado y la solicitud terminó en 500
```

## GREEN

La regla determinista ahora reconoce `deberia` junto con `cambiar`, siempre que la consulta también
contenga un término situacional ya admitido como riego, frecuencia, suelo, humedad o calor. No se
incorporaron otros verbos sin escenarios propios.

```text
python -m pytest tests/unit/test_query.py::test_context_dependent_decisions_request_clarification_without_model tests/unit/test_query.py::test_factual_stage_question_is_not_treated_as_a_situational_decision tests/contract/test_query_api.py::test_situational_irrigation_infinitive_clarifies_without_model_call -q -p no:cacheprovider --basetemp .tmp-bug51-green
# exit 0: 9 passed, 1 warning
```

La prueba factual conserva el caso documental sobre la etapa desde la que conviene aumentar la
frecuencia, evitando convertir toda mención de ajuste de riego en una aclaración situacional.

## REFACTOR y regresión

```text
python -m pytest -q -p no:cacheprovider --basetemp .tmp-bug51-full
# exit 0: 340 passed, 1 skipped, 3 deselected, 1 warning

python -m ruff check src/agro_rag/application/query.py tests/unit/test_query.py tests/contract/test_query_api.py
# exit 0: All checks passed!

python -m ruff format --check src/agro_rag/application/query.py tests/unit/test_query.py tests/contract/test_query_api.py
# exit 0: 3 files already formatted

python -m mypy src
# exit 0: Success: no issues found in 38 source files

lint-imports
# exit 0: 2 contracts kept, 0 broken

git diff --check
# exit 0
```

El skip corresponde a bits POSIX del runner Garak en Windows; los tres casos deseleccionados son
los perfiles e2e/live excluidos de la suite offline.

## Límites

La corrección evita la llamada al LLM para la formulación observada; no pretende resolver mediante
heurísticas todas las paráfrasis posibles. La advertencia conocida pertenece a Starlette/httpx.
No se realizaron nuevas llamadas a OpenAI durante la corrección.
