# Evidencia TDD UI-05 - checklist y runner Playwright

Fecha: 2026-10-28. Responsable y revisor: misma sesión (no hubo revisor independiente
disponible). Rama: `feat/manual-benchmark-runner`.

## Propiedad y alcance

- `scripts/build_benchmark_checklist.py`
- `scripts/run_benchmark_playwright.py`
- `tests/unit/test_benchmark_checklist_pdf.py`
- `tests/unit/test_benchmark_playwright_runner.py`
- PDF, runbook y documentación de evaluación asociados

El runner observa la UI por HTTP/navegador. No importa backend, agentes, índices ni SDK de
modelos. La automatización sólo decide coincidencia de estado; la revisión factual sigue siendo
humana.

## RED

```text
.venv\Scripts\python.exe -m pytest tests/unit/test_benchmark_checklist_pdf.py tests/unit/test_benchmark_playwright_runner.py -q
exit code: 1
2 errores de colección: no existían build_benchmark_checklist ni run_benchmark_playwright.
```

## GREEN

```text
.venv\Scripts\python.exe -m pytest tests/unit/test_benchmark_checklist_pdf.py tests/unit/test_benchmark_playwright_runner.py -q
exit code: 0
4 passed
```

El test reabre el PDF y comprueba 31 páginas, 60 campos Pass, 60 Fail, 60 resultados observados y
60 notas. Los tests del runner fijan carga de 60 casos, clasificación de los tres estados visibles
y semántica de `status_pass`.

## REFACTOR y verificación

Se renderizaron y revisaron visualmente las páginas 1, 2, 16 y 31. La portada, casos iniciales,
casos de aclaración y últimos casos entran en sus cajas sin recortes observados. El PDF final fue
reabierto con `pypdf`: 31 páginas y 244 campos de formulario.

El primer smoke de navegador falló antes de consultar al proveedor: Streamlit exponía `Cultivo`
como combobox personalizado y el selector por label era ambiguo. Se cambió al rol `combobox`, se
agregó RED/GREEN para que cualquier error de ejecución produzca salida no exitosa y se repitió el
caso:

```text
.venv\Scripts\python.exe scripts/run_benchmark_playwright.py --url http://127.0.0.1:8501 --limit 1 --timeout-seconds 90
exit code: 0
dev-r-001: answered (PASS)
```

Verificación final:

```text
ruff check .                                      -> All checks passed
ruff format --check .                             -> 166 files already formatted
pytest (fuera del sandbox para leer el catálogo)  -> 193 passed, 2 deselected
mypy                                              -> Success, 36 source files
lint-imports                                      -> 2 kept, 0 broken
git diff --check                                  -> sin errores
```

Los 59 casos restantes y la calificación humana del PDF continúan pendientes; no se ejecutaron
para evitar costo y latencia de proveedor sin una decisión explícita. Pendiente: commit y CI.
