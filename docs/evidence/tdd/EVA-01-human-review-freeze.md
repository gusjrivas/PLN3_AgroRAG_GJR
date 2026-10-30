# EVA-01: cierre de revisión y benchmark congelado

Fecha: 28/10/2026. Responsable: Gustavo Julián Rivas, con ejecución asistida por Codex y
Playwright. Rama: `eval/freeze-human-benchmark`. Revisión del diff: misma sesión; queda pendiente
revisor independiente antes de integrar.

## Propiedad

- `data/evaluation/benchmark-60.jsonl`
- `tests/unit/test_benchmark_contract.py`
- `README.md`, `docs/plan.md`, `docs/evaluation.md`, `docs/requirements.md`
- `openspec/changes/06-evaluation-delivery/tasks.md`
- este archivo de evidencia

El usuario declaró cerradas las pruebas humanas sobre la planilla local de 60 casos. El primer caso
fue registrado por el usuario y los 59 restantes se ejecutaron una vez mediante Playwright contra
la app local con OpenAI `gpt-4o`. El usuario aceptó ese resultado como cierre. Se declara una sola
aceptación humana y no se calcula acuerdo interanotador.

Resultado de la app: 60/60 estados observados coincidentes, 49 PASS y 11 FAIL después de revisar
contenido factual y fuentes visibles. Los 11 FAIL quedan conservados; no se corrigieron etiquetas
ni se repitieron consultas para mejorar el resultado.

## RED

El primer intento dentro del sandbox falló al leer el catálogo y no se contó como RED funcional.
Repetido con acceso al catálogo:

```text
.venv\Scripts\agro-rag.exe validate-benchmark data\evaluation\benchmark-60-draft.jsonl
exit 1
ValueError: review_status debe ser reviewed
```

Se agregó la prueba de repositorio antes de crear el archivo final:

```text
.venv\Scripts\python.exe -m pytest tests\unit\test_benchmark_contract.py::test_eva_01_repository_final_packet_is_frozen_and_reviewed -q
exit 1
FileNotFoundError: data/evaluation/benchmark-60.jsonl
```

## GREEN

Se creó el paquete final a partir del borrador cambiando únicamente `annotator` y
`review_status`; el borrador permanece intacto.

```text
.venv\Scripts\python.exe -m pytest tests\unit\test_benchmark_contract.py::test_eva_01_repository_final_packet_is_frozen_and_reviewed -q
exit 0
1 passed

.venv\Scripts\agro-rag.exe validate-benchmark data\evaluation\benchmark-60.jsonl
exit 0
case_count=60; split_counts=30/30; category_counts=36/12/12;
pending_human_count=0; review_status=reviewed
```

SHA-256 del benchmark final:
`b12253c38bec4e2e58b20ddb4ec1303c515a360001db37c56e6e54246bdcba69`.
Commit de datos y contrato: `b4010d6` (`test: freeze reviewed benchmark`).

La corrida incremental de los 59 casos automatizados quedó en un artefacto local ignorado por Git:
SHA-256 `747963d8ec9e49dd4e9b3a626ab0b763b801017d94a0d27759bca2eddffca260`,
sin errores, p50 2625 ms y p95 3641 ms. La planilla final local estaba abierta al cerrar esta
evidencia, por lo que no se calculó su hash.

## REFACTOR y regresión

```text
.venv\Scripts\python.exe -m pytest -q
exit 0
215 passed, 2 deselected

.venv\Scripts\python.exe -m mypy src
exit 0
Success: no issues found in 36 source files

.venv\Scripts\python.exe -m ruff check tests\unit\test_benchmark_contract.py
.venv\Scripts\python.exe -m ruff format --check tests\unit\test_benchmark_contract.py
exit 0

.venv\Scripts\lint-imports.exe
exit 0
2 contratos mantenidos, 0 rotos

npx --yes @fission-ai/openspec@latest validate 06-evaluation-delivery --strict
exit 0
```

La suite completa se ejecutó fuera del sandbox y con `.env` oculto/restaurado dentro del mismo
comando. Las corridas anteriores contaminadas por permisos del sandbox o por la clave local no se
contabilizan como regresión del producto.

## Handoff

EVA-01 deja de bloquear EVA-02. El siguiente corte es ejecutar E1/E2/E3 con el benchmark final y
proveedores reales. Antes de E2 o repeticiones se debe fijar un presupuesto porque multiplican
llamadas pagas. Los resultados negativos se publican completos.
