# Evidencia TDD AGT/EVA - estabilidad de decisión generativa

Fecha: 2026-10-28. Responsable y revisor: misma sesión; no hubo revisor independiente disponible.
Rama: `fix/generative-stability`.
Commit de implementación: `c734396`.

## Propiedad y alcance

- `src/agro_rag/application/query.py`
- `src/agro_rag/infrastructure/generation_contract.py`
- `src/agro_rag/infrastructure/openai.py`
- `scripts/run_benchmark_playwright.py`
- pruebas, contratos y OpenSpec asociados

El corte reduce variación de estado sin incorporar IDs ni respuestas del benchmark al producto.
Las etiquetas siguen `pending_human` y no se presentan como verdad científica.

## Línea base live y límite de costo

Se ejecutaron tres repeticiones de `test-r-004`, `test-r-009` y `test-a-006`: nueve consultas
reales en total. `test-r-009` respondió 3/3; `test-r-004` respondió 2/3 y tuvo un error operativo;
`test-a-006` respondió 3/3 aunque esperaba aclaración. La última observación muestra un límite de
referente, no sólo azar de muestreo. Por pedido del usuario no se realizaron más llamadas a OpenAI;
la validación posterior es offline y una repetición live queda pendiente de autorización explícita.

## RED

```text
pytest tests/unit/test_benchmark_playwright_runner.py
exit code: 2, ImportError: summarize_stability ausente

pytest tests/integration/test_openai_model.py tests/unit/test_query.py tests/unit/test_generation_contract.py
exit code: 1, 4 failed, 36 passed
```

Los fallos observables fueron: Responses API sin temperatura fijada, pregunta sin referente no
aclarada, continuación aclarada sin fixture recuperable y prompts sin la política de estado.

## GREEN

```text
pytest tests/integration/test_openai_model.py tests/unit/test_query.py \
  tests/unit/test_benchmark_playwright_runner.py tests/unit/test_generation_contract.py
exit code: 0, 46 passed

pytest -q --basetemp=.tmp/pytest-generative-stability -p no:cacheprovider
exit code: 0, 214 passed, 2 deselected
```

La pregunta elíptica se aclara antes del modelo, pero puede continuar cuando llega
`clarification_context`. OpenAI recibe `temperature=0`; los prompts no confunden hechos
documentales con recomendaciones situacionales. El runner registra `run_index` y genera un resumen
por consulta. Temperatura cero reduce variación, no garantiza determinismo del proveedor.

## REFACTOR y controles

```text
ruff check .                                      -> 0, All checks passed
ruff format --check .                             -> 0, 170 files formatted
mypy                                               -> 0, 36 source files
lint-imports                                       -> 0, 2 contracts kept
openspec validate 04-agents-backend --strict       -> 0, valid
openspec validate 06-evaluation-delivery --strict  -> 0, valid
git diff --check                                   -> 0
```

El índice estructural fue actualizado y no registró problemas en las rutas de aplicación y tests;
el script y la integración HTTP están fuera de los subárboles indexados y se revisaron desde
fuente. La revisión del cambio fue realizada por la misma sesión.
