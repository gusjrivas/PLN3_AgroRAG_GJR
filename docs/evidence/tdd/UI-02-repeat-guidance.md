# Evidencia TDD: consultas sucesivas y guía de UI

Fecha: 24/10/2026. Responsable y revisor disponible: misma sesión Codex; revisión humana
pendiente. Rama: `fix/ui-repeat-guidance`. Propiedad: `src/agro_rag_ui/app.py`, pruebas AppTest y
documentación operativa asociada.

## Alcance

Hacer explícita la diferencia entre exploración de fuentes y respuesta verificada, asociar el
resultado visible con su pregunta y permitir iniciar otra consulta sin reutilizar accidentalmente
estado anterior. Cambiar de modo descarta el resultado previo para evitar una atribución engañosa.
La UI sigue consumiendo únicamente la API HTTP y conserva la clave reader del lado servidor.

## RED

El primer comando focalizado terminó con exit code 1 y `2 failed`: antes del envío no se explicaba
que la exploración no redacta una respuesta y no existía el botón **Nueva consulta**.

```text
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --tb=short --basetemp=.tmp\ui-repeat-red2 tests\ui\test_ui.py::test_preview_explains_mode_and_allows_a_second_query tests\ui\test_ui.py::test_new_query_clears_result_without_calling_api_again
```

Una tercera prueba observable para el cambio de modo también falló con exit code 1: el resultado
de exploración continuaba visible debajo de la explicación del modo verificado.

## GREEN

Se agregó orientación previa, identificación de la pregunta, reinicio explícito del formulario y
limpieza del resultado al cambiar de modo. La llamada permanece ligada exclusivamente al submit.

```text
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --tb=short --basetemp=.tmp\ui-green-final tests\ui\test_ui.py
```

Resultado: exit code 0, `7 passed in 2.39s`.

## REFACTOR y cierre

- Suite completa: exit code 0, `147 passed, 2 deselected in 5.61s`.
- Ruff check/formato: exit code 0, 142 archivos formateados.
- mypy: exit code 0, 32 archivos sin errores.
- import-linter: exit code 0, 2 contratos mantenidos.
- OpenSpec `05-frontend-hardening` estricto: exit code 0.
- Smoke de procesos locales: frontend `http://127.0.0.1:8501` y liveness backend
  `http://127.0.0.1:8000/health/live` respondieron HTTP 200.
- Revisión del impacto con codebase-memory y lectura del diff: misma sesión; revisión humana
  pendiente. El análisis confirmó que el cambio funcional queda en el frontend HTTP; no se
  agregaron dependencias hacia dominio, modelos ni proveedores.

Commit, PR y CI se agregan al cerrar la rama.
