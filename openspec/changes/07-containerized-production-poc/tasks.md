# Tasks: PoC productiva containerizada

Responsable: coordinador de arquitectura. Rama inicial: `feat/v2-container-foundation`. Revisión:
misma sesión durante implementación; revisión humana requerida antes de cada integración. No editar
`Teoria*` ni cambiar contratos funcionales sin un delta separado.

## 0. Contrato

- [x] 0.1 Aceptar ADR-015 y plan V2.
- [x] 0.2 Registrar responsable, rama, propiedad, riesgos y escenarios OpenSpec.
- [x] 0.3 Validar OpenSpec y enlazar evidencia ARC-V2-01 actualizada.

## 1. Configuración y entrypoints

- [x] 1.1 CFG-V2-01 RED: secretos `*_FILE`, conflicto, archivo ausente/vacío y redacción.
- [x] 1.2 CFG-V2-01 GREEN: resolución tipada y fail-closed en API/UI.
- [x] 1.3 ARC-V2-02: caracterizar URL/rutas existentes y proteger límites/runtime read-only.
- [x] 1.4 REFACTOR: tests afectados, typing, arquitectura, docs y evidencia.

## 2. Imágenes

- [x] 2.1 IMG-V2-01 RED/GREEN: Dockerfile multi-stage, targets API/UI, wheel y usuario no root.
- [x] 2.2 IMG-V2-02 RED/GREEN: contexto mínimo, sin secretos/toolchain/dev deps.
- [x] 2.3 Inspección, smoke y evidencia de imagen.

## 3. Compose y catálogo

- [x] 3.1 CMP-V2-01: base/dev, red, healthchecks y arranque healthy.
- [x] 3.2 DAT-V2-01: volumen persistente, API read-only y job admin idempotente.
- [x] 3.3 CMP-V2-02: E2E offline, reinicio y compatibilidad V1.

## 4. Producción y seguridad

- [x] 4.1 SEC-V2-01: gateway único, segmentación, secretos mínimos y hardening.
- [x] 4.2 OPS-V2-01: readiness, versión de release y logs estructurados.
- [x] 4.3 OPS-V2-02: backup/restore y rollback probado.

## 5. CI, staging y garak

- [x] 5.1 CI-V2-01: build/test/Compose/SBOM/escaneo/publicación por SHA/semver.
- [x] 5.2 SEC-V2-02: runner, adaptador, configuración, parser/gate y tests offline.
- [ ] 5.3 Ejecutar staging limpio y scan autorizado; registrar resultados reales separados.
- [ ] 5.4 Promover la misma imagen y completar documentación/release sólo con evidencia.

Preparación de 5.3: workflows manuales de publicación del runner, smoke de release y scan protegido
implementados; preflight y bootstrap/restore del host limpio documentados. No se marca completa
hasta registrar su ejecución en un host real y un reporte real autorizado.
