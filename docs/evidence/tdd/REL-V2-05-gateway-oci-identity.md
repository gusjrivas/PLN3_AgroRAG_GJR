# REL-V2-05 — identidad OCI del gateway detectada por preflight

Fecha: 30/10/2026. Responsable: coordinador de arquitectura. Rama:
`fix/v2-gateway-release-labels`. Propiedad: Dockerfile, inspección CI, contratos de imagen,
OpenSpec/runbook y esta evidencia. Revisión técnica realizada por la misma sesión; revisión humana
requerida antes de integrar.

## RED operacional

Se preparó Ubuntu 26.04.1 WSL2 como rehearsal single-host: Docker Engine 29.5.2/Compose 5.1.3,
14 CPU, 16 GB RAM, puertos 80/443 libres y checkout Linux limpio. Los tres digests publicados para
`5a11a29` se descargaron y un catálogo aislado se publicó offline con 27 evidencias y versión
`e9929440f552b1c7be1349118a1ee98c6cdba41fbd2e2ce05343247c918dfb7d`.

El preflight real bloqueó antes de `up`:

```text
single-host preflight blocked: AGRO_GATEWAY_IMAGE no pertenece al commit esperado
exit 1
```

La inspección por digest demostró que API/UI llevaban revisión y versión `5a11a29`, pero gateway
conservaba `version=v2.11.7` de la imagen Caddy y no tenía
`org.opencontainers.image.revision`. No se relajó el preflight ni se desplegó la candidata.

El ensayo también caracterizó dos condiciones operativas:

- un checkout montado desde Windows tenía CRLF y no era un checkout Linux válido; se clonó `main`
  en ext4 de WSL;
- el backup inicialmente falló porque el directorio `0700` era UID 1000; al asignarlo al UID/GID
  runtime `10001:10001`, produjo un ZIP `0600` de 22.492 bytes con 27 evidencias. El runbook ahora
  documenta esa propiedad.

## RED de contrato

Se agregaron primero contratos que exigen versión/revisión OCI dentro del stage gateway y que CI
compruebe la revisión de API/UI/gateway:

```text
uv run pytest \
  tests/architecture/test_container_image_contract.py::test_gateway_v2_carries_the_same_release_identity_as_api_and_ui \
  tests/architecture/test_container_ci_contract.py::test_ci_v2_builds_once_tests_the_images_and_emits_supply_chain_evidence \
  -q --tb=short
exit 1: 2 failed
```

## GREEN

Implementación: `8333fd93fe1378f91868eeb2389c508e051cb917`.

El stage gateway redeclara `APP_VERSION`, `VCS_REF` y `SOURCE_URL` y sobrescribe las labels OCI de
Caddy con la identidad de AgroRAG. El workflow compara la revisión de las tres imágenes con
`GITHUB_SHA` antes de E2E/SBOM/scan/publicación.

```text
suite dirigida de imagen/CI/preflight          12 passed
build local target gateway                     exit 0
revision                                       1111111111111111111111111111111111111111
version                                        0.2.0-test
user                                           10002:10002
```

## REFACTOR y regresión

```text
uv run pytest -q                               281 passed, 3 deselected, 1 warning
uv run ruff check .                            exit 0
uv run ruff format --check .                   exit 0; 224 files
uv run mypy                                    exit 0; 38 source files
uv run lint-imports                            exit 0; 2 contracts kept
npx --yes @fission-ai/openspec@1.14.3 validate --all --strict
                                                exit 0; 8 passed, 0 failed
actionlint 1.7.12                               exit 0
git diff --check                               exit 0
```

## Estado

La candidata `5a11a29` queda rechazada para staging porque su gateway carece de identidad OCI. Este
corte debe integrarse y publicar nuevos digests coherentes; sólo entonces se repetirá preflight,
`up`, smoke, backup/restore y Garak. No se atribuye evidencia positiva a una imagen aún no publicada.
