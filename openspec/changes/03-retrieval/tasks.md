# Tasks: Recuperación híbrida y reranking evaluables

Responsable: RAG/datos. Dependencias: 02-corpus. Primera implementación parcial en PR #4. Evidencia: docs/evidence/tdd/03-05-first-version.md. Mantener casillas abiertas hasta cubrir todos los escenarios, incluidos proveedores reales, índice híbrido y hardening pendientes.

## 1. Preparación

- [ ] 1.1 Leer ADR aplicables, fijar archivos de propiedad y comprobar dependencias.
- [ ] 1.2 Preparar fixtures/contratos sin servicios pagos; identificar qué checks requieren integración real.

## 2. Implementación mediante TDD

- [ ] 2.1.1 RED: escribir y ejecutar pruebas de los escenarios de RET-01; guardar fallo funcional esperado.
- [ ] 2.1.2 GREEN: implementar mínimo comportamiento de RET-01 y ejecutar las mismas pruebas.
- [ ] 2.1.3 REFACTOR: mejorar diseño, ejecutar suite afectada/typing/imports y registrar evidencia de RET-01.
- [ ] 2.2.1 RED: escribir y ejecutar pruebas de los escenarios de RET-02; guardar fallo funcional esperado.
- [ ] 2.2.2 GREEN: implementar mínimo comportamiento de RET-02 y ejecutar las mismas pruebas.
- [ ] 2.2.3 REFACTOR: mejorar diseño, ejecutar suite afectada/typing/imports y registrar evidencia de RET-02.
- [ ] 2.3.1 RED: escribir y ejecutar pruebas de los escenarios de RET-03; guardar fallo funcional esperado.
- [ ] 2.3.2 GREEN: implementar mínimo comportamiento de RET-03 y ejecutar las mismas pruebas.
- [ ] 2.3.3 REFACTOR: mejorar diseño, ejecutar suite afectada/typing/imports y registrar evidencia de RET-03.

## 3. Cierre

- [ ] 3.1 Ejecutar tests de integración/seguridad pertinentes y checks estáticos; distinguir mocks de proveedores reales.
- [ ] 3.2 Actualizar documentación, trazabilidad y handoff; enlazar evidencia y commit.
- [ ] 3.3 Revisión del diff por revisor disponible, registrar autor y riesgos; integrar cuando Definition of Done esté satisfecha.
- [ ] 3.4 Archivar el cambio y promover deltas a specs sólo después de verificar implementación real.
