# Evidencia TDD: hardening operativo y presupuesto Garak

Fecha: 30/10/2026 (America/Buenos_Aires). Responsable y revisión técnica: misma sesión
coordinadora; revisión humana pendiente. Rama: `fix/garak-harness-hardening`. Base:
`8ca5a5f23d4f935b388c526c5740b10f509ad160`. Propiedad: adaptador/runner Garak, perfil security,
contratos, runbook y esta evidencia. No se modificaron contratos funcionales de `/v1/query`.

Commit de implementación: `8a992ecf482b55e187e16626cb17feb5c72a1636` (`fix: harden garak
scan budget and evidence`). MR: #35.

## Hallazgo real que inicia el cambio

La primera corrida local autorizada contra la release `41ba62f` comenzó el 31/10/2026 01:33:26Z y
se detuvo por el timeout formal de 60 minutos. El gateway registró 129 POST: 39 respuestas 200, 90
respuestas 422 y ninguna 5xx. El JSONL parcial restringido quedó fuera de Git, con 77 líneas,
100.115 bytes, SHA-256
`c357af938257e48dec8a7a5cce6498c6b9a6302fab88cf88d24ba7385d20872e` y modo corregido a `0600`.
No se produjo resumen y la corrida se clasificó `BLOCKED`; no es evidencia de aprobación.

El análisis sin imprimir prompts mostró que `dan.DanInTheWild` incluye entradas mayores que el
límite público de 2.000 caracteres. El API las rechazó correctamente con 422, pero el adaptador
traducía todo error a 502 y Garak reintentó el mismo caso. No se amplió ni debilitó el contrato
público. El costo de esa corrida previa no pudo medirse con el harness anterior; por ello no se
realiza otra llamada paga hasta validar el nuevo control fail-closed.

## RED

Se escribieron primero casos observables para rechazo 422, errores no recuperables, timeout interno,
permisos desde el primer byte, resumen sanitizado y métricas. El primer comando dirigido produjo
`6 failed, 6 passed`. Luego se agregó el requisito del usuario de no superar USD 0,20: el comando

```text
.\.venv\Scripts\python.exe -m pytest tests/unit/test_garak_adapter.py -q
```

terminó con exit 1, `7 failed, 5 passed`. Los siete fallos fueron la ausencia de
`max_cost_usd`, reserva previa, conciliación de usage y validación del techo; no se fabricó una fase
roja sobre implementación existente.

## GREEN y REFACTOR

El adaptador ahora:

- devuelve una negativa estable para 422 y lo cuenta como `contract_rejected`, evitando el bucle de
  retries sin alterar `/v1/query`;
- reserva de forma thread-safe USD 0,12 antes de cada request, peor caso de 12.000 tokens a la
  tarifa de salida de GPT-4o; considera costo observado y reservas en vuelo;
- fija la tarifa oficial verificada de GPT-4o en USD 2,50/M input y USD 10/M output, y rechaza todo
  techo mayor que USD 0,20;
- libera la reserva de un 422, concilia respuestas válidas mediante `usage` y cobra la reserva
  completa ante errores ambiguos;
- no llama al gateway cuando una reserva excedería el techo, cuenta `budget_exhausted` y provoca
  que el runner bloquee con `cost_budget_exhausted`.

El runner establece `umask 077` antes de crear evidencia, limita la ejecución a 3.300 segundos,
recupera métricas agregadas y escribe un resumen sanitizado bloqueante aun ante timeout, salida no
cero, reporte ausente, error del adaptador o presupuesto agotado. Los crudos parciales se fuerzan a
`0600`; los resúmenes no contienen prompts, respuestas ni secretos.

Comandos ejecutados sin acceso a OpenAI:

```text
.\.venv\Scripts\python.exe -m pytest tests/unit/test_garak_adapter.py tests/unit/test_garak_runner.py tests/architecture/test_garak_container_contract.py -q
# exit 0: 21 passed, 1 skipped (permiso POSIX, no aplicable en Windows)

.\.venv\Scripts\python.exe -m ruff check scripts/garak_adapter.py scripts/run_garak.py tests/unit/test_garak_adapter.py tests/unit/test_garak_runner.py tests/architecture/test_garak_container_contract.py
# exit 0

$env:MYPYPATH='scripts'; .\.venv\Scripts\python.exe -m mypy src scripts/garak_adapter.py scripts/run_garak.py
# exit 0: Success: no issues found in 40 source files

.\.venv\Scripts\python.exe -m pytest -q
# exit 0: 297 passed, 1 skipped, 3 deselected

uv run lint-imports
# exit 0: 2 contracts kept, 0 broken

npx --yes @fission-ai/openspec@1.14.3 validate 07-containerized-production-poc --strict
# exit 0: change valid
```

El intento de ejecutar `openspec` como binario global terminó con exit 1 porque no está instalado
en Windows; se repitió con la versión fijada anterior. Del mismo modo,
`python -m lint_imports` no es el entrypoint del paquete y terminó con exit 1; `uv run lint-imports`
es el comando correcto y aprobó.

## Imagen Linux y smokes offline

La imagen `agrorag-garak:budget-cap` se construyó para `linux/amd64` desde un worktree ext4,
reutilizando la capa de dependencias fijadas. Identidad local:

```text
sha256:006fa5b1afc673a59f05d2b0fb61221c5f7a17628ed559bbf833fcbe66d552f6
3.291.110.680 bytes
UID:GID 10003:10003
garak 0.17.0
```

Smokes dentro de esa imagen, todos con exit 0 y sin red de proveedor:

- `umask 077` creó `/tmp/raw.report.jsonl` con modo `0o600` desde el primer byte;
- un transporte simulado con HTTP 422 devolvió la negativa contractual, registró una sola
  `contract_rejected`, cero tokens y cero nano-USD;
- con techo USD 0,11, menor que la reserva conservadora USD 0,12, `generate` devolvió
  `budget_exhausted`, dejó costo cero y no invocó el transporte centinela.

Fuente primaria de precios consultada el 30/10/2026:
https://developers.openai.com/api/docs/models/gpt-4o. No se infirió la tarifa desde memoria ni se
realizó una llamada de prueba al proveedor.

CI del MR #35 sobre el commit de implementación:

- `quality`, run `41163000279`: `offline`, `specs` y `browser` aprobaron;
- `container-supply-chain`, run `41163000386`: `build-test-scan-publish` aprobó en 2m33s.

## Estado y límites

Este corte corrige el harness y documenta el primer bloqueo; no completa OpenSpec 5.3. La imagen
Linux y la suite completa están validadas localmente. Falta integrar/publicar un nuevo digest y,
con confirmación humana, hacer como máximo una nueva corrida real bajo el techo USD 0,20. Alcanzar
el techo es un resultado bloqueante, no una aprobación. Garak continúa siendo evidencia heurística,
no certificación ni garantía de seguridad.
