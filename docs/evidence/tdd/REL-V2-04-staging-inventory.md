# REL-V2-04 — inventario sanitizado de staging

Fecha: 30/10/2026. Responsable: coordinador de arquitectura. Rama:
`feat/v2-container-foundation`. Propiedad: preflight single-host, contrato Linux del preflight,
workflow de contenedores y documentación REL-V2. Revisión realizada por la misma sesión; se mantiene
la revisión humana obligatoria antes de integrar el MR #30.

## Escenario y RED

La auditoría de REL-V2-01 encontró que el runbook exigía registrar host/CPU/memoria, imágenes,
digests y tiempos, pero la salida aprobada del preflight sólo contenía release, commit y volumen.
Se amplió primero `tests/architecture/test_single_host_preflight.py` para exigir un deployment ID no
sensible, esquema de evidencia, instante/duración, recursos y las tres referencias por digest:

```text
uv run pytest tests/architecture/test_single_host_preflight.py -q --tb=short
exit 1: 3 failed, 1 passed
```

Los tres fallos observaron la ausencia del nuevo contrato en script y plantilla. Después se agregó
un segundo test para exigir que CI ejecutara la rama aprobada dentro de Linux, no sólo `sh -n`:

```text
uv run pytest \
  tests/architecture/test_single_host_preflight.py::test_container_ci_executes_the_approved_preflight_branch \
  -q --tb=short
exit 1: fixture/runner Linux ausente
```

## GREEN

Implementación: `850bc196330ccdd3cc8510b6a4db4b468b195a96`.

El preflight requiere `AGRO_DEPLOYMENT_ID` con caracteres seguros y, sólo después de aprobar todas
las precondiciones, emite pares `clave=valor` con esquema, UTC, duración, kernel/arquitectura,
CPU/memoria, Docker/Compose, release/commit/volumen y digests API/UI/gateway. Omite dominio, modelo,
ruta de secretos y contenidos. El runbook exige `umask 077` y destino restringido.

El contrato Linux usa un Docker determinista simulado para recorrer inspect de usuario/label,
volumen y Compose sin daemon, registry ni proveedor. Además introduce secretos centinela y bloquea
si alguno aparece en el inventario.

```text
uv run pytest tests/architecture/test_single_host_preflight.py -q
5 passed in 0.02s

docker run --rm --entrypoint sh -v <repo>:/workspace:ro \
  agrorag-gateway:staging-verifier \
  /workspace/tests/container/run_preflight_contract.sh \
  /workspace/scripts/preflight_single_host.sh
exit 0; schema/status/deployment/release/commit y tres digests verificados
```

## REFACTOR y regresión

```text
uv run pytest -q                            280 passed, 3 deselected, 1 warning
uv run ruff check .                         exit 0
uv run ruff format --check .                exit 0; 223 files
uv run mypy                                 exit 0; 38 source files
uv run lint-imports                         exit 0; 2 contracts kept
npx --yes @fission-ai/openspec@1.14.3 validate --all --strict
                                             exit 0; 8 passed, 0 failed
actionlint 1.7.12                            exit 0
git diff --check                             exit 0
```

Codebase Memory reportó el script como excluido y los archivos nuevos/modificados como no tracked
en su snapshot de cobertura. Por eso se verificaron directamente fuentes, diff, ejecución Linux y
tests; no se usa ausencia de hallazgos del grafo como prueba.

## Límite de la evidencia

El Docker simulado prueba el contrato del preflight, no inventario de un host real. La tarea 5.3
permanece abierta hasta conservar este archivo generado en staging junto con smoke, reinicio,
backup/restore, rollback, scan Garak autorizado y dictamen humano.
