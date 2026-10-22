# FND-01/02/03: base Python

Responsable y revisión: sesión Codex, sin revisor independiente. Rama feat/00-foundation. Base remota f9ce97af91c74d8a0198372da531d3b990c62b5d.

- FND-01: clon independiente confirmado, sin cambios previos ni escrituras al repositorio docente. Operación Git preexistente: no se atribuye TDD a git clone. No se ha copiado código docente.
- RED: `uv run pytest tests/contract/test_health.py -q`; dos fallos funcionales porque /health/live devolvía 404. Log: 00-red.txt. El scaffold FastAPI sólo creaba una app vacía.
- GREEN: mismo test tras incorporar router de salud: dos aprobados. Log: 00-green.txt.
- REFACTOR: router separado del ensamblado. `uv run pytest --cov -q`: 2 aprobados, 100% de 11 sentencias. No es cobertura representativa del futuro RAG.
- `uv run mypy`: sin errores en 9 módulos; Ruff lint/formato correctos. `uv run lint-imports`: dos contratos respetados.
- `uv sync --frozen --offline`: correcto. Instalación adicional en virtualenv vacío desde cache, suite sin credenciales. La instalación inicial requiere red; las pruebas no consultan servicios externos.
- `uv run pip-audit --local --skip-editable`: ninguna vulnerabilidad conocida al ejecutar. Política: cualquier hallazgo bloquea cierre hasta resolverlo o documentar una excepción justificada; no ignorar IDs automáticamente. La auditoría consulta fuentes externas y no integra la suite offline.

Advertencia observada: Starlette anuncia futura sustitución de httpx en TestClient; no impide esta versión fijada. No hay readiness, corpus ni frontend funcional todavía.

Los logs preservan los resultados originales. La CI repite lint, formato, typing, imports, tests con cobertura y validación OpenSpec. Los controles cubren comportamiento y formato, pero no pueden demostrar por sí solos que los tests se escribieron antes: cada PR debe incluir evidencia RED real.
