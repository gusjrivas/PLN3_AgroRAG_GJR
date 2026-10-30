# Evidencia TDD: automatización de publicación y gate Garak en staging

Fecha: 30/10/2026. Responsable y revisión: misma sesión coordinadora; revisión humana pendiente en
MR #30. Rama: `feat/v2-container-foundation`. Propiedad: workflows Garak, contratos de arquitectura,
runbook, plan, seguridad y esta evidencia.

Commit de implementación: `a8fac27` (`ci: automate authorized garak staging gate`).

## RED

Se escribieron primero tres contratos en
`tests/architecture/test_garak_release_workflows.py`. El comando
`uv run pytest tests/architecture/test_garak_release_workflows.py -q --tb=short` terminó con exit 1
y `3 failed`: faltaban `.github/workflows/garak-runner.yml` y
`.github/workflows/staging-security.yml`. El RED exigía build/scan/publicación del mismo runner,
referencia por digest, autorización explícita, secrets por archivo, cifrado del crudo, retenciones
separadas, cleanup incondicional y acciones externas fijadas a commits completos.

## GREEN

- `garak-runner-supply-chain` es manual y exige reconocer el build grande. Construye una vez en
  `linux/amd64`, verifica UID 10003, versión/revisión, genera SBOM, reescanea con Trivy 0.76.1 y
  aplica la política aislada antes de autenticar/publicar.
- Publica el mismo tag local únicamente como `sha-<commit>`, vuelve a resolverlo por digest y crea
  `garak-runner-manifest.json`; no existe `latest` ni un rebuild posterior al scan.
- `staging-garak-security-gate` exige confirmación, environment protegido, target HTTPS exacto,
  release segura y el paquete Garak del mismo repositorio por `@sha256`. Reescanea ese digest antes
  de recibir los secretos de ensayo.
- Las tres credenciales se escriben en archivos efímeros `0600`; Compose usa `--no-build`. El raw se
  cifra con AES-256-CBC/PBKDF2 antes del upload y se conserva 7 días; el resumen sanitizado se
  conserva 90. Ningún upload apunta a `raw/` y el directorio temporal se elimina con `always()`.
- Garak puede fallar sin perder evidencia: el scan permite continuar hasta cifrar/subir, y un paso
  final restaura el resultado bloqueante si faltó aprobación, raw o resumen.

Resultados focalizados:

- `uv run pytest tests/architecture/test_garak_release_workflows.py -q`: exit 0, `3 passed`.
- actionlint oficial 1.7.12 sobre los cuatro workflows: exit 0, sin hallazgos.
- `docker compose -f compose.security.yaml --profile security config --quiet`: exit 0 con valores
  sintéticos, sin ejecutar red ni proveedor.
- `npx --yes @fission-ai/openspec@1.14.3 validate --all --strict`: exit 0, `8 passed`.

## REFACTOR y regresión

Se eliminó el uso de `runner.temp` en un contexto no garantizado y se deriva el directorio desde
`RUNNER_TEMP` dentro del shell. La referencia de imagen se valida como prefijo exacto del paquete
GHCR esperado más 64 hex, evitando aceptar un paquete arbitrario capaz de leer secretos.

`uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy` y `uv run lint-imports`
terminaron con exit 0; mypy revisó 38 archivos y los dos contratos de imports se mantuvieron. La
suite completa terminó con exit 0: `263 passed, 3 deselected, 1 warning in 15.58s`.
`git diff --check` también terminó con exit 0.

## Límite y siguiente evidencia

No se ejecutaron los workflows manuales ni un ataque real. No hay staging/dominio/TLS, credenciales
de ensayo, presupuesto/proveedor ni autorización aportados, por lo que no se fabrican manifiesto,
reporte, triage ni dictamen. OpenSpec 5.3 y 5.4 siguen abiertos. Para cerrar 5.3 se debe registrar el
host Linux limpio, digests de producto/runner, run de GitHub, costo, resumen y revisión humana; para
5.4 se deben promover exactamente los mismos digests y probar salud/rollback.
