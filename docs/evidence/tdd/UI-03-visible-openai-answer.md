# Evidencia TDD: respuesta OpenAI visible

Fecha: 24/10/2026. Responsable y revisor disponible: misma sesión Codex; revisión humana
pendiente. Rama: `feat/openai-provider`. Propiedad: `src/agro_rag_ui/app.py`, pruebas AppTest y
documentación operativa asociada.

## Alcance

Hacer visible el resultado de **Respuesta verificada** sin exigir que la persona descubra que debe
desplazarse debajo del formulario. La respuesta, su confirmación de OpenAI y las fuentes se ubican
antes del formulario, que permanece disponible para consultas sucesivas. La UI continúa usando
exclusivamente la API HTTP y no recibe la API key de OpenAI.

## Diagnóstico real

Los registros mostraron tres `POST /v1/query` con HTTP 200. Una reproducción con Chrome headless
confirmó que el encabezado y el resultado existían, pero quedaban debajo del formulario y fuera del
área visible habitual. La integración real respondió `answered`, decisión `approve`, una cita y dos
llamadas al modelo.

## RED

```text
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --tb=short --basetemp=.tmp\ui-visible-red tests/ui/test_ui.py::test_verified_answer_is_prominent_and_identifies_openai
```

Exit code 1: no existía confirmación visible que identificara OpenAI.

## GREEN

Se reservó un contenedor de resultado antes del formulario y se agregó la confirmación
`Respuesta lista: generada y verificada con OpenAI.`. Se reemplazaron selectores posicionales
frágiles de AppTest por etiquetas observables.

```text
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --tb=short --basetemp=.tmp\ui-suite-green3 tests/ui/test_ui.py
```

Exit code 0: `8 passed in 7.78s`.

## Verificación visual

Chrome headless contra los procesos reales confirmó, con scroll inicial en cero, que el resultado,
el encabezado, la fuente y **Nueva consulta** están visibles antes del formulario. La consulta real
usó OpenAI; no se incluyeron secretos ni el cuerpo de la respuesta en los registros de evidencia.

## REFACTOR y cierre

- Suite completa: exit code 0, `165 passed, 2 deselected in 15.41s`.
- Ruff check: exit code 0.
- Ruff format check: exit code 0, 150 archivos sin cambios.
- mypy: exit code 0, 34 archivos sin errores.
- import-linter: exit code 0, 2 contratos mantenidos.
- UI y liveness local: HTTP 200 en `127.0.0.1:8501` y `127.0.0.1:8010`.
- Revisión funcional y visual: misma sesión; revisión humana pendiente.

