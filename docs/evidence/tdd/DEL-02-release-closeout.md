# Evidencia TDD: cierre técnico de release

Fecha: 29/10/2026. Responsable y revisión: misma sesión coordinadora; no hubo un revisor técnico
independiente disponible. Rama: `chore/release-closeout`. Propiedad: typing del generador PDF,
documentación de cierre, OpenSpec y libros Excel de evidencia.

## RED de typing

El alcance de mypy se amplió al generador PDF y a los runners E1/E2/E3:

```powershell
.venv\Scripts\python.exe -m mypy src scripts/run_e1_retrieval.py scripts/run_e2_budgeted.py scripts/run_e3_cache.py scripts/build_report.py
```

Resultado inicial: exit 1, 10 errores en `scripts/build_report.py`. Mypy detectó stubs ausentes de
ReportLab, tres firmas incompletas y una llamada no tipada. El primer GREEN dejó un error real de
`PropertySet` frente a `ParagraphStyle`; se corrigió con un cast acotado en el borde del SDK.

## GREEN

Se añadió `types-reportlab` al grupo `dev`, se tiparon estilos, canvas, documento, flowables y tabla,
y se regeneró `uv.lock`. El mismo comando terminó con exit 0: `Success: no issues found in 40
source files`.

## Libros Excel

Se consolidaron sin reexportar los tres `.xlsx` locales en `docs/evidence/workbooks/`. Los hashes y
el propósito de cada libro están en el README de esa carpeta. La revisión E2 completada por el
usuario conserva 18/18 filas con revisor y fecha.

## Cierre y verificación

Commit de implementación: `4faf306533d40f56da068ef78cc207036f9b2fda`. MR:
[#28](https://github.com/gusjrivas/PLN3_AgroRAG_GJR/pull/28).

Se creó un worktree detached limpio en una ruta temporal, sin `.env`, y se verificó exactamente ese
commit:

- `uv sync --frozen`: exit 0, 95 paquetes instalados.
- `pytest -q`: exit 0, `220 passed, 2 deselected`.
- mypy ampliado: exit 0, 40 archivos sin errores.
- Ruff check y format check: exit 0, 73 archivos ya formateados.
- import-linter: exit 0, 2 contratos mantenidos.
- OpenSpec `validate --all --strict`: exit 0, 7/7 ítems válidos.
- `agro-rag verify-delivery --root .`: exit 0, 8 artefactos.
- integridad ZIP de los tres `.xlsx`: exit 0.
- `git status --short` en el worktree: salida vacía.

La primera suite en el árbol principal tuvo un único fallo porque el `.env` privado local contiene
la clave que el test de “clave ausente” intenta retirar sólo del entorno del proceso. El mismo test
y la suite completa aprobaron en el checkout limpio; no se cambió el producto para ocultar esa
contaminación local.

El punto académico humano —ensayo de 15 minutos, modalidad, fecha de Teoría 7 y eventual correo—
permanece deliberadamente fuera de este cierre técnico. El tag `v0.1.0` se crea únicamente sobre el
merge aprobado del MR final.
