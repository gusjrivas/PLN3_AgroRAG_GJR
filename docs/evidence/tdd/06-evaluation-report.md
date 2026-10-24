# Evidencia TDD: contrato de reporte EVA-02

Fecha: 24/10/2026. Responsable y revisor disponible: misma sesión Codex; revisión humana
pendiente. Rama: `feat/06-evaluation-report`. Propiedad: módulo/pruebas del reporte EVA-02,
documentación de evaluación y trazabilidad OpenSpec 06.

## Alcance

Se automatiza el reporte reproducible de E1/E2/E3: variantes congeladas, consultas pareadas,
procedencia real/doble, corpus/dataset/commit, versiones de prompt/modelos, estado o error por
pregunta, tokens, latencia p50/p95 y métricas etiquetadas por recuperación, generación, agentes u
operación. Las comparaciones publican denominador, casos excluidos y deltas negativos.

Los fixtures son sintéticos. No se ejecutaron proveedores ni se atribuye calidad real; esa fase
depende del benchmark de 60 casos anotado y revisado por humanos.

## RED

Comando:
`.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=.tmp\eva02-red tests\unit\test_evaluation_report.py`.

Resultado: exit code 1, `3 failed`; `agro_rag.evaluation.report` no existía.

## GREEN

Se agregaron `MetricObservation`, `QueryObservation`, `EvaluationReport`, `build_report` y
`write_report`.

Comando:
`.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=.tmp\eva02-green tests\unit\test_evaluation_report.py`.

Resultado: exit code 0, `3 passed in 0.03s`.

## REFACTOR y cierre

- La primera revisión focalizada conservó los 3 tests verdes y detectó formato y una anotación
  mypy; ambos se corrigieron.
- Ruff y mypy focalizados: exit 0.
- Suite completa: exit 0, `141 passed, 2 deselected in 4.72s`.
- Ruff check/formato: exit 0, 134 archivos formateados.
- mypy: exit 0, 31 archivos sin errores.
- import-linter: exit 0, 2 contratos mantenidos.
- OpenSpec 06 estricto: válido, exit 0.
- CI: pendiente de registrar antes de integrar.
- Revisión del diff: misma sesión; revisión humana pendiente.

## Limitaciones

- `execution_kind=real` y `human_reviewed=true` son declaraciones de procedencia que el artefacto
  conserva; la revisión operativa debe contrastarlas con manifiestos y evidencia del run.
- El reporte no elige parámetros ni sustituye la anotación humana.
