# EVA-01: paquete para revisión humana

Fecha: 28/10/2026. Responsable y revisión: misma sesión Codex; revisión agronómica humana pendiente.
Rama: `feat/eva01-human-review-packet`. Base: `1a2203b`. Propiedad: contrato/CLI de benchmark,
paquete candidato, pruebas y documentación EVA-01. No se usaron proveedores ni secretos.

## RED

Primero se exigió un cargador distinto para borradores completos, capaz de validar balance e IDs sin
aceptarlos como benchmark revisado:

`.venv\Scripts\python.exe -m pytest -q tests/unit/test_benchmark_contract.py`

Salida 1: `2 failed, 3 passed`; `load_benchmark_draft` no existía.

Luego se exigió una entrada operativa para que el revisor valide el archivo sin escribir Python:

`.venv\Scripts\python.exe -m pytest -q tests/unit/test_benchmark_contract.py::test_cli_validates_draft_packet_without_promoting_it`

Salida 1: `1 failed`; argparse rechazó `validate-benchmark` como comando inexistente.

## GREEN

Se agregó un contrato `BenchmarkDraft` separado. Exige exactamente el mismo muestreo 60/30/30 y
18/6/6 por split que EVA-01, resuelve todas las evidencias y obliga a que cada fila sea
`pending_human`. `load_benchmark` sigue exigiendo `reviewed`, por lo que no existe promoción
implícita. El CLI informa estado, conteos, versión y SHA-256.

El paquete `data/evaluation/benchmark-60-draft.jsonl` contiene 36 casos respondibles, 12 sin soporte
y 12 ambiguos/adversariales. Sus referencias son candidatas preparadas desde los 27 fragmentos del
catálogo activo; no constituyen anotación humana ni resultado de calidad.

Comando focalizado final:

`.venv\Scripts\python.exe -m pytest -q tests/unit/test_benchmark_contract.py`

Salida 0: `7 passed`.

Validación directa del artefacto: 60 casos; dev/test `30/30`; categorías `36/12/12`; 60
`pending_human`; SHA-256 `302fadb5f41680eb19ad221789868afc8cd5a3e4d6f82b16ed8dd0f08fcd199c`.

## REFACTOR y cierre técnico

- `.venv\Scripts\python.exe -m pytest --cov --cov-report=term-missing`: salida 0,
  `188 passed, 2 deselected`, cobertura global `88.37%`.
- `.venv\Scripts\coverage.exe report --include='src/agro_rag/domain/*,src/agro_rag/application/*' --fail-under=90`:
  salida 0, cobertura domain/application `96%`.
- Ruff lint/formato: salida 0; 160 archivos formateados.
- Mypy: salida 0, 36 archivos sin errores.
- Import-linter: salida 0, dos contratos mantenidos.
- OpenSpec 1.14.3 estricto: salida 0, siete cambios válidos.
- `verify-delivery`: salida 0, ocho artefactos; PDF SHA-256
  `38e3ff63cc82d32bdcb3666c3cdb8b361a000cb81cbf2151ac09b322fcd5f76`.

Una primera invocación manual de cobertura con módulos explícitos no combinó la ejecución de
Streamlit y produjo `83.31%` con `app.py` artificialmente en 0%. Se repitió exactamente el comando
de CI (`pytest --cov`), que combinó AppTest y obtuvo `88.37%`; no se cambió el umbral ni se excluyó
código. El PDF regenerado conserva siete páginas y fue inspeccionado completo, con revisión en
detalle de las páginas 4 y 5; no se observaron cortes, superposiciones ni páginas vacías.
La repetición final de `test_delivery.py` encontró primero una denegación del sandbox sobre el
directorio temporal de pytest; fuera de ese límite operativo terminó con `3 passed`.

El primer check `offline` del PR #23 aportó un RED de checkout limpio: `2 failed, 186 passed`.
Las dos pruebas nuevas intentaban leer `data/processed/catalogue`, un artefacto runtime ignorado que
no existe en CI. Se reemplazó esa dependencia por un catálogo fixture en memoria construido para el
contrato del paquete; la validación operativa local sigue usando el catálogo activo real. El comando
focalizado posterior terminó con `7 passed` y no se incorporaron snapshots runtime al repositorio.

Commit de implementación: `6160259` (`feat: prepare EVA-01 human review packet`).

## Límite y siguiente puerta

La sesión autora también hizo la revisión técnica; no sustituye al revisor humano de contenido. Antes
de E1/E2/E3 una persona debe contrastar las 60 filas con las páginas fuente, corregirlas, identificarse
como anotador y recién entonces cambiar cada estado a `reviewed`. No se declara EVA-01 completo.
