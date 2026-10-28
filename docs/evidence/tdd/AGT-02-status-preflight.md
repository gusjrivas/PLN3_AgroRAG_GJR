# Evidencia TDD AGT-02 - decisión previa de estado

Fecha: 2026-10-28. Responsable y revisor: misma sesión; no hubo revisor independiente disponible.
Rama: `fix/benchmark-status-gate`.
Commit de implementación: `0ae744e`.

## Propiedad y alcance

- `src/agro_rag/application/query.py`
- `tests/unit/test_query.py`
- contrato y OpenSpec asociados

El corte aborda siete desacuerdos observados en la corrida Playwright de 60 casos. Las etiquetas
del benchmark continúan `pending_human`: se preservan como expectativa provisional y no se las
promueve a revisión humana por esta corrección.

## RED

```text
.venv\Scripts\python.exe -m pytest tests/unit/test_query.py -q
exit code: 1
7 failed, 20 passed
```

Los siete escenarios devolvían otro estado o intentaban consumir el modelo aun cuando el fixture
entregaba evidencia lexical coincidente.

## GREEN

```text
.venv\Scripts\python.exe -m pytest tests/unit/test_query.py -q
exit code: 0
27 passed
```

La decisión previa normaliza acentos y mayúsculas, separa temas fuera del corpus de decisiones
contextuales incompletas y no llama al modelo. Un control adicional demuestra que la misma
pregunta situacional continúa al flujo investigador/verificador cuando recibe cultivo, etapa y
descripción del suelo.

## Verificación live y estabilidad

Los siete casos originales pasaron en una corrida Playwright dirigida. La primera regresión
completa posterior produjo 57/60 y reveló tres decisiones adicionales; se generalizó la política
para recomendaciones comerciales, valores actuales imposibles de inferir sin medición y lecturas
de sensor sin unidad. Los casos nuevos quedaron cubiertos por RED/GREEN y pasaron dirigidos.

Las regresiones completas posteriores produjeron 58/60 y 57/60, pero con IDs diferentes que habían
pasado en ejecuciones previas. Esto se registra como inestabilidad residual del componente
generativo, no como cero FAIL ni como calidad científica. No se agregaron reglas por cada frase.

## REFACTOR y controles

```text
.venv\Scripts\python.exe -m ruff check .                         -> 0, All checks passed
.venv\Scripts\python.exe -m ruff format --check .                -> 0, 168 files formatted
.venv\Scripts\python.exe -m mypy                                -> 0, 36 source files
.venv\Scripts\lint-imports.exe                                  -> 0, 2 contracts kept
.venv\Scripts\python.exe -m pytest -q --basetemp=.tmp/pytest-benchmark-fixes-closure -p no:cacheprovider
                                                               -> 0, 210 passed, 2 deselected
git diff --check                                                -> 0
```

La revisión factual humana de respuestas y etiquetas continúa fuera de este corte. La revisión
del cambio fue realizada por la misma sesión; no hubo revisor independiente disponible.
