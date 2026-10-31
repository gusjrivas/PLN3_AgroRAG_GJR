# Evidencia TDD: plataforma reproducible para CI V2

Fecha: 31/10/2026 (America/Buenos_Aires). Responsable y revisión técnica: misma sesión
coordinadora; revisión humana pendiente. Rama: `fix/ci-ubuntu-24-04`. Base:
`9de01719035c7fae80f7c56fe1742ea2b8d1d415`. Propiedad: workflows GitHub Actions, contrato de
arquitectura asociado, documentación y esta evidencia. Commit de implementación:
`e5519ef` (`ci: pin GitHub runners to Ubuntu 24.04`).

## Incidente observado

Después de integrar el hardening de Garak, el run de `quality`
[`41225299377`](https://github.com/gusjrivas/PLN3_AgroRAG_GJR/actions/runs/41225299377) y el de
`container-supply-chain`
[`41225299345`](https://github.com/gusjrivas/PLN3_AgroRAG_GJR/actions/runs/41225299345) del commit
`9de0171` fallaron antes de probar/publicar la candidata. GitHub asignó Ubuntu 26.04 a
`ubuntu-latest`, pero Playwright 1.56.0/1.56.1 rechazó la instalación de Chromium para esa imagen.
No se publicaron imágenes de producto de ese commit y no se lo considera candidato para Garak.

La corrección fija `ubuntu-24.04` en los jobs de calidad, supply chain, publicación del runner
Garak, smoke de staging y scan protegido. No cambia dependencias, producto, contrato HTTP ni
presupuesto. La etiqueta explícita está soportada por GitHub y evita que una migración de
`ubuntu-latest` cambie la plataforma sin revisión.

## RED

Se agregó primero `test_ci_v2_linux_workflows_pin_the_supported_runner_image`, que exige que cada
workflow Linux use `ubuntu-24.04` y prohíbe `ubuntu-latest`.

```text
uv run pytest tests/architecture/test_container_ci_contract.py -q
# exit 1: 1 failed, 3 passed
# fallo esperado: ci.yml todavía contenía runs-on: ubuntu-latest
```

El fallo es observable y corresponde al drift real del runner; no es un error de credenciales ni
una historia reconstruida.

## GREEN

Se sustituyó únicamente el selector de runner en los cinco workflows versionados.

```text
uv run pytest tests/architecture/test_container_ci_contract.py -q
# exit 0: 4 passed
```

## REFACTOR y validación

Verificaciones ejecutadas en la rama, sin acceso a OpenAI ni a otro proveedor pago:

```text
uv run pytest -q
# exit 0: 298 passed, 1 skipped, 3 deselected

uv run ruff check .
# exit 0: All checks passed

uv run mypy
# exit 0: Success: no issues found in 38 source files

uv run lint-imports
# exit 0: 2 contracts kept, 0 broken

npx --yes @fission-ai/openspec@1.14.3 validate 07-containerized-production-poc --strict
# exit 0: change valid

git diff --check
# exit 0
```

El único `skip` es el control de bits POSIX del runner Garak que no aplica en Windows. Los tres
casos deseleccionados son pruebas marcadas fuera de la suite offline; no se ejecutaron scans reales.

## GREEN remoto del MR

El primer HEAD documentado del MR #37 aprobó sobre la plataforma fijada:

- `quality`, run
  [`41226199536`](https://github.com/gusjrivas/PLN3_AgroRAG_GJR/actions/runs/41226199536): `specs`
  8 s, `browser` 33 s y `offline` 51 s, todos `success`;
- `container-supply-chain`, run
  [`41226199572`](https://github.com/gusjrivas/PLN3_AgroRAG_GJR/actions/runs/41226199572): build, E2E,
  SBOM, scans y política aprobaron en 2m41s.

En un evento `pull_request` la publicación es correctamente omitida. Después del merge todavía se
debe comprobar que el run de `main` publique el manifiesto inmutable del nuevo commit; hasta
entonces no se reconstruye ni ejecuta Garak.

