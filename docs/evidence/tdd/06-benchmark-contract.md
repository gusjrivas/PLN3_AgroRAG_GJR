# Evidencia TDD: contrato EVA-01

Fecha: 24/10/2026. Responsable y revisor disponible: misma sesión Codex; revisión humana
pendiente. Rama: `feat/06-benchmark-contract`. Propiedad: módulo y pruebas del contrato EVA-01,
documentación de evaluación y trazabilidad OpenSpec 06.

## Alcance

Se automatiza lo verificable antes de la anotación: esquema cerrado, 60 IDs únicos, splits dev/test
de 30 casos, composición 18 respondibles/6 sin soporte/6 adversariales por split, aislamiento de
familias, resolución de evidencia y SHA-256 del JSONL. Los casos sin soporte o adversariales no
pueden contener qrels y se separan del denominador IR.

No se crean preguntas ni etiquetas. El conjunto humano revisado, EVA-02 y la entrega DEL-01
siguen pendientes.

## RED

Comando: `.venv\Scripts\python.exe -m pytest -q tests\unit\test_benchmark_contract.py`.

Resultado: exit code 1, `3 failed`; `agro_rag.evaluation.benchmark` no existía.

## GREEN

Se agregó `BenchmarkCase`, `BenchmarkDataset` y `load_benchmark`. Comando, ejecutado con un
directorio temporal aislado por una ACL defectuosa del TEMP global:

```text
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=.tmp\pytest-benchmark-green tests\unit\test_benchmark_contract.py
```

Resultado: exit code 0, `3 passed in 0.10s`.

## REFACTOR y cierre

- Ruff focalizado: exit 0.
- mypy focalizado: exit 0, un archivo sin errores.
- Suite completa en sandbox: `127 passed, 2 deselected` y 11 errores de lectura del catálogo por
  ACL; se registró como fallo de harness, no como resultado funcional.
- Suite completa con acceso al catálogo: exit 0, `138 passed, 2 deselected in 8.84s`.
- Ruff check y formato: exit 0, 131 archivos formateados.
- mypy: exit 0, 30 archivos sin errores.
- import-linter: exit 0, 2 contratos mantenidos.
- OpenSpec 06 estricto: válido, exit 0.
- Commit funcional: `55c825a`. PR [#12](https://github.com/gusjrivas/PLN3_AgroRAG_GJR/pull/12).
- CI del commit funcional: `specs`, `offline` y `browser` aprobados.
- Revisión del diff: misma sesión; revisión humana pendiente.

## Limitaciones

- Los fixtures sintéticos sólo prueban invariantes; no son evidencia de calidad del sistema.
- El benchmark no se considera congelado hasta incorporar 60 casos efectivamente anotados y
  revisados contra el corpus definitivo.
