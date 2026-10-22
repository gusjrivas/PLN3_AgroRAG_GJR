# Tasks: Recuperación híbrida y reranking evaluables

Responsable: RAG/datos. Dependencias: 02-corpus. Primera implementación parcial en PR #4. Evidencia: docs/evidence/tdd/03-05-first-version.md. Mantener casillas abiertas hasta cubrir todos los escenarios, incluidos proveedores reales, índice híbrido y hardening pendientes.

## Corte independiente: contratos offline

Responsable: coordinador/RAG, misma sesión. Rama: feat/03-retrieval-contracts. Propiedad y límites: docs/plan.md y ADR-013. Evidencia: docs/evidence/tdd/03-pipeline.md.

- [x] C.1 Leer contratos/ADR y verificar corpus descargado y base main.
- [x] C.2 RED: cuatro modos, fallo vector, identidad de índice, filtros, diversidad y presupuesto.
- [x] C.3 GREEN/REFACTOR: pipeline por puertos, candidatos lexicales y errores controlados; suite y checks locales.
- [ ] C.4 CI remota y revisión del diff; integrar sólo con checks aprobados.
- [ ] C.5 Adaptadores reales, tokenizer, prefijos E5, evaluación en español y activación por bootstrap (otro PR).

Los checks del corte no cierran los requisitos completos siguientes.

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
