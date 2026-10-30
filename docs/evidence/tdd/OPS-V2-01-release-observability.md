# Evidencia TDD: identidad y observabilidad de release

Fecha: 29/10/2026. Responsable y revisión: misma sesión coordinadora; revisión humana pendiente en
MR #30. Rama: `feat/v2-container-foundation`. Propiedad: settings de release, bootstrap API,
Dockerfile/Compose, contratos y documentación operativa.

## RED

El primer contrato observable añadió `/health/version` y un evento HTTP JSON sanitizado:

```powershell
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .tmp/pytest-ops-v2-red tests/contract/test_operability.py
```

Resultado: exit 1, `2 failed`: el endpoint devolvía 404 y no existía el evento. Un segundo RED de
imagen/Compose produjo `3 failed`: faltaban `--no-access-log`, metadata de build y variables
productivas.

## GREEN y refactor

- `/health/version` devuelve semver, commit, referencia/digest de imagen y catálogo activo.
- Cada respuesta recibe un UUID en `X-Request-ID` y registra una línea JSON con campos cerrados.
- No se registra query string, headers, body o secretos; el access log duplicado de Uvicorn queda
  desactivado.
- Docker propaga `APP_VERSION`/`VCS_REF`; producción exige versión/commit y usa la referencia API
  inmutable como identidad de imagen.
- Liveness/readiness y los contratos HTTP anteriores no cambian.

Suite dirigida: exit 0, `12 passed`; Ruff y mypy: exit 0.

## Smoke de imagen real

Se construyó `agrorag-api:ops-v2-test` con versión `2.0.0-rc.1` y commit sintético de 40 caracteres.
`GET /health/version` devolvió esos valores, catálogo nulo e imagen `unknown` (correcto fuera del
overlay productivo). `docker logs` incluyó una línea JSON `http_request_completed`, path
`/health/version`, estado 200 y duración; no apareció access log del request. El contenedor temporal
se detuvo y eliminó con `--rm`.

La identidad expuesta es trazabilidad operativa, no prueba por sí sola que el registry sirvió ese
digest; CI/promoción deben contrastar el manifiesto inmutable.
