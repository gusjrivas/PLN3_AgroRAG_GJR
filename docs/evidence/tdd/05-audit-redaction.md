# Evidencia TDD: auditoría estructurada y redacción

Fecha: 24/10/2026. Responsable y revisor disponible: misma sesión Codex; revisión humana pendiente.
Rama: `feat/05-retrieval-cache`, ampliación del PR #11.

## Alcance y propiedad

Completar `OPS-01-redaccion` con un puerto application, evento cerrado y adaptador JSON inyectado
desde bootstrap. Archivos principales:

- `src/agro_rag/application/audit.py`
- `src/agro_rag/infrastructure/audit.py`
- `src/agro_rag/application/query.py`
- `src/agro_rag/bootstrap/app.py`
- `tests/unit/test_audit.py`

No se registra pregunta, contexto, evidencia, prompt, URL, clave ni mensaje de excepción.

## RED

Comando: `.venv\Scripts\python.exe -m pytest -q tests\unit\test_audit.py`.

Resultado: exit code 1, `3 failed`: `QueryService` no aceptaba sink, el módulo de contrato no existía
y tampoco había adaptador de logging.

## GREEN

Se agregó `QueryAuditEvent`, `AuditSink`, registro de finalización/error con tipo allowlisted y
`LoggingAuditSink`. Comando afectado:

```text
.venv\Scripts\python.exe -m pytest -q tests\unit\test_audit.py tests\unit\test_query.py
```

Resultado: exit code 0, `20 passed in 0.43s`.

La revisión detectó que el error HTTP podía generar un request_id distinto al evento. Se agregaron
dos pruebas RED: excepción sin correlación y `ErrorResponse` con UUID diferente (`2 failed`). GREEN:
la excepción transporta sólo el request_id opaco y la API lo reutiliza, `14 passed` en auditoría y
contrato HTTP.

## REFACTOR y cierre

Resultados locales:

- Suite inicial: error de harness por ACL del TEMP global; no se contó como resultado funcional.
- Suite con basetemp aislado: exit 0, `135 passed, 2 deselected`.
- Ruff check/formato: exit 0, 128 archivos formateados.
- mypy: exit 0, 29 archivos sin errores. Durante REFACTOR detectó y se corrigió el tipo abierto del
  resultado auditado para usar `AuditOutcome`.
- import-linter: exit 0, 2 contratos mantenidos.
- OpenSpec 05 estricto: válido, exit 0.

La revisión fue realizada por la misma sesión. Pendiente registrar commit, actualización del PR #11
y CI remota.

## Límites

- En errores antes de completar la respuesta se registran contadores en cero; no se fabrican
  mediciones parciales.
- El adaptador emite al logger estándar. Rotación y retención pertenecen a la configuración del
  proceso anfitrión.
