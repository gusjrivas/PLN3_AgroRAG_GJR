# Tasks: Interfaz Python, seguridad y optimización

Responsable: Frontend y revisor. Dependencias: 04-agents-backend; UI puede preparar fixtures desde contratos congelados. Primera implementación parcial en PR #4. Evidencia: docs/evidence/tdd/03-05-first-version.md. Mantener casillas abiertas hasta cubrir todos los escenarios, incluidos proveedores reales, índice híbrido y hardening pendientes.

## Corte independiente: caché observable de retrieval

Responsable: coordinador/backend, misma sesión. Rama: `feat/05-retrieval-cache`. Propiedad:
`src/agro_rag/application/query.py`, `tests/unit/test_query.py`, ADR-010, documentación y evidencia
`docs/evidence/tdd/05-retrieval-cache.md`. El PR también promueve a `main` el hardening ya revisado
del PR #10, cuyo merge quedó en una rama intermedia.

- [x] R.1 RED: hit normalizado observable, invalidación por cultivo/versión y errores no cacheados.
- [x] R.2 GREEN: LRU acotado por instancia, clave versión+consulta normalizada+cultivo y escritura
  sólo después de retrieval exitoso.
- [x] R.3 REFACTOR: suite, typing, arquitectura, OpenSpec, revisión del diff y CI remota.

Este corte satisface `OPS-01-hit` e `OPS-01-invalidate`. `OPS-01-redaccion` permanece abierto hasta
incorporar y verificar el sink de auditoría; la redacción HTTP de retrieval ya está cubierta por #10.

## Corte de auditoría estructurada y redacción

Responsable: coordinador/backend, misma sesión. Rama: `feat/05-retrieval-cache`, ampliación del PR
#11. Propiedad: `src/agro_rag/application/audit.py`, `src/agro_rag/infrastructure/audit.py`,
`src/agro_rag/application/query.py`, bootstrap, pruebas y evidencia
`docs/evidence/tdd/05-audit-redaction.md`.

- [x] A.1 RED: evento de negocio seguro, error centinela redactado y salida JSON de esquema cerrado.
- [x] A.2 GREEN: puerto `AuditSink`, evento inmutable sin texto y adaptador logging ensamblado desde
  bootstrap.
- [x] A.3 REFACTOR: suite, typing, arquitectura, OpenSpec, revisión y CI remota.

Con este corte quedan cubiertos los tres escenarios observables de OPS-01; las tareas generales de
05 permanecen abiertas hasta cerrar UI/SEC y la evidencia integral del cambio.

## Corte independiente: consultas sucesivas y guía de uso

Responsable y revisor disponible: coordinador/frontend, misma sesión. Rama:
`fix/ui-repeat-guidance`. Propiedad: `src/agro_rag_ui/app.py`, `tests/ui/test_ui.py`, documentación
operativa y evidencia `docs/evidence/tdd/UI-02-repeat-guidance.md`.

- [x] U.1 RED: guía previa ausente, reinicio inexistente y resultado obsoleto al cambiar de modo.
- [x] U.2 GREEN: instrucciones por modo, pregunta asociada, nueva consulta y limpieza al cambiar.
- [x] U.3 REFACTOR: AppTest, suite, typing, arquitectura, OpenSpec y revisión del impacto.

Este corte amplía `UI-01-respuesta` y `UI-02-rerun`; no cierra por sí solo los demás escenarios
generales del cambio.

## 1. Preparación

- [ ] 1.1 Leer ADR aplicables, fijar archivos de propiedad y comprobar dependencias.
- [ ] 1.2 Preparar fixtures/contratos sin servicios pagos; identificar qué checks requieren integración real.

## 2. Implementación mediante TDD

- [ ] 2.1.1 RED: escribir y ejecutar pruebas de los escenarios de UI-01; guardar fallo funcional esperado.
- [ ] 2.1.2 GREEN: implementar mínimo comportamiento de UI-01 y ejecutar las mismas pruebas.
- [ ] 2.1.3 REFACTOR: mejorar diseño, ejecutar suite afectada/typing/imports y registrar evidencia de UI-01.
- [ ] 2.2.1 RED: escribir y ejecutar pruebas de los escenarios de UI-02; guardar fallo funcional esperado.
- [ ] 2.2.2 GREEN: implementar mínimo comportamiento de UI-02 y ejecutar las mismas pruebas.
- [ ] 2.2.3 REFACTOR: mejorar diseño, ejecutar suite afectada/typing/imports y registrar evidencia de UI-02.
- [ ] 2.3.1 RED: escribir y ejecutar pruebas de los escenarios de SEC-01; guardar fallo funcional esperado.
- [ ] 2.3.2 GREEN: implementar mínimo comportamiento de SEC-01 y ejecutar las mismas pruebas.
- [ ] 2.3.3 REFACTOR: mejorar diseño, ejecutar suite afectada/typing/imports y registrar evidencia de SEC-01.
- [ ] 2.4.1 RED: escribir y ejecutar pruebas de los escenarios de OPS-01; guardar fallo funcional esperado.
- [ ] 2.4.2 GREEN: implementar mínimo comportamiento de OPS-01 y ejecutar las mismas pruebas.
- [ ] 2.4.3 REFACTOR: mejorar diseño, ejecutar suite afectada/typing/imports y registrar evidencia de OPS-01.

## 3. Cierre

- [ ] 3.1 Ejecutar tests de integración/seguridad pertinentes y checks estáticos; distinguir mocks de proveedores reales.
- [ ] 3.2 Actualizar documentación, trazabilidad y handoff; enlazar evidencia y commit.
- [ ] 3.3 Revisión del diff por revisor disponible, registrar autor y riesgos; integrar cuando Definition of Done esté satisfecha.
- [ ] 3.4 Archivar el cambio y promover deltas a specs sólo después de verificar implementación real.
