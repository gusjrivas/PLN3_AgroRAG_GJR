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

Los comandos finales, sus códigos de salida, el commit, el MR y el tag se completan al terminar la
verificación de rama y CI. El punto académico humano —ensayo de 15 minutos, modalidad, fecha de
Teoría 7 y eventual correo— permanece deliberadamente fuera de este cierre técnico.
