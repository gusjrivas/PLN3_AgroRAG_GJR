# REL-V2-03 — preflight de host productivo single-host

Fecha: 30/10/2026. Responsable: coordinador de arquitectura. Rama:
`feat/v2-container-foundation`. Archivos de propiedad: preflight, plantilla de deploy, contrato de
arquitectura asociado, workflow de contenedores y documentación V2. Revisión realizada por la misma
sesión; continúa requerida revisión humana antes de integrar el MR #30.

## Escenario observable

`REL-V2-clean-host-preflight` exige que un host Linux falle antes de `compose up` si Engine/Compose
no responde, una imagen no está fijada por digest o no corresponde al commit/usuario esperado, el
volumen externo no existe, los secretos tienen permisos laxos o el Compose productivo no renderiza.
El control no debe crear recursos, descargar imágenes, restaurar datos ni imprimir secretos.

## RED

Se escribió primero `tests/architecture/test_single_host_preflight.py` y se ejecutó:

```text
uv run pytest tests/architecture/test_single_host_preflight.py -q --tb=short
exit 1: 3 failed
```

Los fallos observables fueron la ausencia de `scripts/preflight_single_host.sh`, de
`infra/deploy/production.env.example` y del parseo Linux en CI. Durante GREEN aparecieron dos
aserciones demasiado amplias del test: confundían `printenv` con ejecutar `env` y exigían una
representación textual distinta pero equivalente de `sh -n`. Se estrecharon para comprobar el
riesgo real; no se relajó ninguna precondición del preflight.

## GREEN

El commit de implementación es `290dbb383d295dfd56e6e5a82677a3b444280e2c`. Agrega:

- preflight POSIX fail-closed, read-only y ejecutable;
- plantilla sin valores secretos para las referencias/configuración productivas;
- bootstrap desde backup aprobado y orden operativo documentado;
- parseo del script dentro de la imagen Linux del gateway en supply chain CI.

Resultados dirigidos:

```text
uv run pytest tests/architecture/test_single_host_preflight.py -q
3 passed in 0.03s

docker run --rm --entrypoint sh -v <script>:/tmp/preflight_single_host.sh:ro \
  agrorag-gateway:staging-verifier -n /tmp/preflight_single_host.sh
exit 0

docker run --rm --entrypoint sh -v <script>:/tmp/preflight_single_host.sh:ro \
  agrorag-gateway:staging-verifier /tmp/preflight_single_host.sh
exit 1: single-host preflight blocked: Docker Engine no está instalado
```

La segunda ejecución caracteriza el fallo sanitizado dentro de un contenedor que no posee Docker;
no pretende sustituir la ejecución sobre el host staging real.

## REFACTOR y regresión

```text
uv run pytest -q
278 passed, 3 deselected, 1 warning in 12.91s

uv run ruff check .                         exit 0
uv run ruff format --check .                exit 0; 222 files formatted
uv run mypy                                 exit 0; 38 source files
uv run lint-imports                         exit 0; 2 contracts kept
npx --yes @fission-ai/openspec@1.14.3 validate --all --strict
                                             exit 0; 8 passed, 0 failed
actionlint 1.7.12                            exit 0
git diff --check                             exit 0
```

Codebase Memory se consultó como control estructural. El snapshot disponible era anterior a este
commit y marcó el script como excluido/no tracked; por eso las afirmaciones sobre script, Compose,
workflow y tests se verificaron directamente contra sus fuentes. No se infiere cobertura del grafo.

## Límites pendientes

Este corte automatiza precondiciones pero no completa la tarea 5.3. Falta ejecutar el preflight en
un host Linux limpio con sus digests/volumen/secretos reales, levantar la candidata, probar
TLS/smoke/reinicio/backup/restore/rollback y ejecutar Garak con autorización y triage humano. Tampoco
crea environments o secretos de GitHub ni autoriza costos de proveedor.
