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
- [x] 5.3 Ejecutar staging limpio y scan autorizado; registrar resultados reales separados.
- [ ] 5.4 Promover la misma imagen y completar documentación/release sólo con evidencia.

Preparación de 5.3: workflows manuales de publicación del runner, smoke de release y scan protegido
implementados; preflight, inventario sanitizado y bootstrap/restore del host limpio documentados.
No se marca completa hasta registrar su ejecución en un host real y un reporte real autorizado.

Corte REL-V2-06: responsable coordinador, rama `fix/preflight-secret-ownership`; propiedad sobre
preflight, contrato container, workflow CI y documentación de despliegue. El preflight real detectó
que los secretos `0600` del operador no eran legibles por los UID no-root; el contrato ahora exige
`10001:10001` para API/UI y `10002:10002` para gateway. La tarea 5.3 continúa abierta hasta Garak.

Ejecución REL-V2-07: el primer scan Garak real local autorizado de `41ba62f` quedó `BLOCKED` tras
60 minutos, 90 respuestas 422 de 129 POST y ausencia de resumen. El raw parcial se restringió a
`0600`; 5.3 permanece abierta hasta corregir el harness, repetir y completar triage humano.

Corte SEC-V2-03: el primer scan real alcanzó el timeout al reintentar rechazos 422 de prompts fuera
del contrato público. El hardening convierte ese rechazo en resultado observable, protege el crudo
desde su primer byte, genera resumen bloqueante ante timeout/error y aplica antes de cada request un
techo fail-closed de USD 0,20. La tarea 5.3 sigue abierta hasta reconstruir el runner, repetir una
única corrida autorizada dentro de ese techo y completar el triage humano.

Corte CI-V2-02: los checks post-merge de `9de0171` detectaron drift de `ubuntu-latest` a Ubuntu
26.04, incompatible con la versión bloqueada de Playwright, antes de publicar imágenes. Los cinco
workflows Linux fijan `ubuntu-24.04` y un contrato impide volver a usar la etiqueta móvil. La tarea
5.3 continúa abierta hasta integrar el corte, aprobar CI remoto y publicar la candidata exacta.

Ejecución REL-V2-08: `d38814b4` publicó y desplegó producto/runner por digest. La corrida autorizada
terminó `BLOCKED` en USD 0,080445: la reserva siguiente habría elevado el total a USD 0,200445 y no
se llamó al gateway. API key cubrió 32 casos reales sin detección; DAN dejó 15 respuestas reales
marcadas y Base64/prompt injection no tuvieron llamadas reales. Los crudos permanecen restringidos
y sólo se versionan resúmenes sanitizados. Gus Rivas cerró el triage DAN el 31/10/2026: 15/15
falsos positivos, 0 confirmados y 0 dudosos. La ejecución real y su revisión completan 5.3 con
resultado bloqueante; 5.4 sigue abierta por cobertura incompleta y no hay retry autorizado.

Seguimiento REL-V2-08: el usuario autorizó hasta USD 0,50 adicionales y se mantuvo el techo técnico
de USD 0,20 por corrida. Las ejecuciones dirigidas y una recuperación limitada a los 12 intentos
interrumpidos completaron Base64 32/32 y prompt injection 32/32 con respuestas reales y 0
detecciones. El gasto nuevo fue USD 0,256830. La deuda de cobertura queda resuelta; 5.4 permanece
abierta hasta realizar la promoción formal de la misma imagen y cerrar la release con evidencia.

Seguimiento solicitado por el usuario: después de cerrar y documentar esta corrida, revisar cómo
implementar lo pedido por la profesora. Es un pendiente de relevamiento; no se asume alcance ni se
marca como parte completada de 5.3 hasta contar con el pedido concreto.
