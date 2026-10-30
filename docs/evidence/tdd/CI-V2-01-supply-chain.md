# Evidencia TDD: CI y supply chain de contenedores

Fecha: 30/10/2026. Responsable y revisión: misma sesión coordinadora; revisión humana pendiente en
MR #30. Rama: `feat/v2-container-foundation`. Propiedad: workflows, gateway base, política de
vulnerabilidades, contratos, runbook y esta evidencia.

Commit de implementación: `f0c9c05` (`ci: build scan and publish immutable images`).

## RED

El contrato `tests/architecture/test_container_ci_contract.py` falló con `3 failed` porque
`.github/workflows/containers.yml` no existía. La política ejecutable comenzó con `2 failed` por
ausencia de `scripts.check_vulnerability_policy`.

El primer scan real con Trivy 0.76.1 fue un RED de seguridad útil: API no tuvo HIGH/CRITICAL, pero
Caddy 2.11.4 reportó 3 hallazgos Alpine (uno CRITICAL) y 25 HIGH del binario. No se ocultó ni se
declaró aprobado.

## GREEN y diseño del gate

- Build único de API/UI/gateway; el mismo tag local alimenta E2E, SBOM, scan y publicación.
- SBOM SPDX JSON y Trivy JSON son artefactos de 30 días; el manifiesto de digests se conserva 90.
- Publicación GHCR sólo desde push, por `sha-<commit>` y semver válido; no existe `latest` ni rebuild.
- Acciones externas fijadas a commits completos; checkout no persiste credenciales.
- CRITICAL y secretos bloquean sin excepción. HIGH requiere riesgo, owner, tracking y fecha vigente;
  una excepción vencida bloquea automáticamente.

Pruebas de contrato/política: exit 0, `6 passed`. Actionlint 1.7.12 validó `ci.yml` y
`containers.yml` con exit 0.

## Remediación y scan local

Se actualizó el gateway al Caddy oficial 2.11.7 por digest y se aplicaron actualizaciones Alpine.
Trivy confirmó 0 HIGH/CRITICAL en API y UI. Gateway quedó con 0 CRITICAL y 6 registros HIGH/5 CVE
únicos en el binario upstream. La política aceptó temporalmente esos cinco IDs con responsable
Gustavo Julián Rivas y vencimiento 15/11/2026; Caddyfile validó dentro de la imagen no root.

La excepción no equivale a resolución. Antes del vencimiento se debe consumir el primer Caddy
oficial corregido, reescanear y retirar entradas. La ejecución real del nuevo workflow, publicación
GHCR y manifest remoto se registrarán después del push; este documento no los anticipa.
