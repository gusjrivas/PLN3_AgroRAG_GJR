# REL-V2-06 — propietarios runtime de secretos y despliegue real

Fecha: 2026-10-30/31. Responsable: coordinador. Rama:
`fix/preflight-secret-ownership`. Propiedad: `scripts/preflight_single_host.sh`, su contrato
container/CI, documentación de arquitectura, OpenSpec y runbook. Commit: pendiente de integración.
Revisión: misma sesión; revisión humana requerida antes de integrar.

## Hallazgo real previo al cambio

El primer `docker compose ... up -d --wait --no-build` de la candidata `41ba62f` creó los tres
servicios, pero API terminó no saludable. Su log indicó:

```text
AGRO_READER_KEY_FILE debe apuntar a un archivo legible
```

Los archivos eran regulares, no vacíos y `0600`, por lo que el preflight vigente los había
aprobado. Sin embargo, pertenecían al UID del operador (`1000`) y API/UI ejecutan como
`10001:10001`; gateway ejecuta como `10002:10002`. Se corrigieron fuera del repositorio los
propietarios, se comprobó lectura dentro de las tres imágenes y Compose alcanzó `healthy`. La UI
autenticada respondió 200; `/health/version` informó commit `41ba62f91d972d839342e0e531fddba16963fb82`
y `/v1/corpus` informó 27 evidencias.

## RED

Primero se amplió `tests/architecture/test_single_host_preflight.py` para exigir inspección
`%u:%g` y el mapeo exacto de cada secreto. Ejecución:

```text
uv run pytest tests/architecture/test_single_host_preflight.py -q --tb=short
exit 1
1 failed, 4 passed
assert "stat -c '%u:%g'" in script
```

El fallo fue funcional y esperado: el script sólo comprobaba modo `0400|0600`.

## GREEN

`check_secret` conserva las validaciones de archivo regular, no symlink, no vacío y modo
restrictivo, y ahora falla cerrado si el propietario numérico no coincide:

- `reader_key` y `openai_api_key`: `10001:10001`.
- `gateway_auth`: `10002:10002`.

El contrato ejecutable crea fixtures con esos propietarios, cambia temporalmente cada archivo a la
identidad del otro servicio, exige los tres rechazos sanitizados y luego exige aprobación al
restaurar cada propietario correcto.
El job CI usa root únicamente para preparar ownership de fixtures; el preflight de producción no
requiere root y continúa read-only.

```text
uv run pytest tests/architecture/test_single_host_preflight.py -q --tb=short
exit 0
5 passed

docker run --rm --user 0:0 ... \
  sh tests/container/run_preflight_contract.sh scripts/preflight_single_host.sh
exit 0
single-host preflight blocked: reader_key debe pertenecer a 10001:10001
single-host preflight blocked: openai_api_key debe pertenecer a 10001:10001
single-host preflight blocked: gateway_auth debe pertenecer a 10002:10002
schema=agrorag.single-host-preflight.v1
status=approved
```

La línea de rechazo es una aserción del escenario negativo y no contiene valores secretos.

## Validación real

Se ejecutó el script corregido en Ubuntu WSL2 contra las imágenes ya publicadas por digest, el
volumen restaurado y los secretos corregidos. Resultado real, no mock:

```text
exit 0
schema=agrorag.single-host-preflight.v1
status=approved
checked_at_utc=2026-10-31T00:56:39Z
deployment_id=wsl-staging-a
engine_version=29.5.2
compose_version=5.1.3
release=0.2.0-sha.41ba62f91d972d839342e0e531fddba16963fb82
commit=41ba62f91d972d839342e0e531fddba16963fb82
catalogue_volume=agrorag_catalogue_staging_5a11a29
```

Los tres digests completos fueron validados y emitidos por el inventario; se omiten aquí porque ya
están registrados en `REL-V2-05`. El stack continuó saludable durante la comprobación.

## REFACTOR y documentación

Se reemplazó el loop duplicado por `check_secret`, se mantuvo la salida aprobada sin propietarios ni
rutas sensibles y se actualizaron arquitectura, plan V2, requisitos, OpenSpec y runbook. La tarea
5.3 sigue abierta: este corte completa preflight/despliegue local, no el scan Garak real autorizado.

```text
uv run pytest -q                               281 passed, 3 deselected, 1 warning
uv run ruff check .                            exit 0
uv run ruff format --check .                   exit 0; 226 files
uv run mypy                                    exit 0; 38 source files
uv run lint-imports                            exit 0; 2 contracts kept
npx --yes @fission-ai/openspec@1.14.3 validate --all --strict
                                                exit 0; 8 passed, 0 failed
actionlint 1.7.12                               exit 0
git diff --check                               exit 0
```

