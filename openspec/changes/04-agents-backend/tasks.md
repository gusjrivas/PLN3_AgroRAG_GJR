# Tasks: API y colaboración de dos agentes

Responsable: Backend/agentes. Dependencias: 03-retrieval. Primera implementación parcial en PR #4. Evidencia: docs/evidence/tdd/03-05-first-version.md. Mantener casillas abiertas hasta cubrir todos los escenarios, incluidos proveedores reales, índice híbrido y hardening pendientes.

## Corte independiente: proveedor OpenAI

Responsable y revisor disponible: coordinador/backend, misma sesión. Rama `feat/openai-provider`.
Propiedad: configuración/bootstrap, contratos compartidos de generación, adaptador OpenAI, pruebas,
ADR-014 y evidencia `docs/evidence/tdd/AGT-04-openai-provider.md`.

- [x] O.1 RED: adaptador y selección de proveedor inexistentes (`7 failed`).
- [x] O.2 GREEN: Responses API estructurada, readiness sin generación y Ollama preservado.
- [x] O.3 REFACTOR: suite, typing, arquitectura, OpenSpec y revisión local.
- [ ] O.4 LIVE: ejecutar una consulta real sólo con key, acceso y costo autorizados.

## Corte independiente: decisión previa de estado

Responsable y revisor disponible: coordinador/backend, misma sesión. Rama:
`fix/benchmark-status-gate`. Propiedad: `src/agro_rag/application/query.py`,
`tests/unit/test_query.py`, contratos, OpenSpec y evidencia
`docs/evidence/tdd/AGT-02-status-preflight.md`.

- [x] S.1 RED: reproducir los siete desacuerdos de estado aun con evidencia lexical disponible.
- [x] S.2 GREEN: resolver alcance y contexto situacional antes de llamar al modelo.
- [x] S.3 REFACTOR: suite, typing, arquitectura, corrida live dirigida y revisión del diff.

## Corte independiente: estabilidad de decisión generativa

Responsable y revisor disponible: coordinador/backend, misma sesión. Rama:
`fix/generative-stability`. Propiedad: preflight, contrato generativo, adaptador OpenAI, runner de
benchmark, pruebas y evidencia `docs/evidence/tdd/AGT-EVAL-generative-stability.md`.

- [x] G.1 RED: reproducir referente ausente, muestreo no fijado y falta de resumen repetido.
- [x] G.2 GREEN: aclaración determinista, prompts de estado, `temperature=0` y resumen estable.
- [x] G.3 REFACTOR: suite offline, typing, arquitectura y documentación sin llamadas live extra.

## 1. Preparación

- [ ] 1.1 Leer ADR aplicables, fijar archivos de propiedad y comprobar dependencias.
- [ ] 1.2 Preparar fixtures/contratos sin servicios pagos; identificar qué checks requieren integración real.

## 2. Implementación mediante TDD

- [ ] 2.1.1 RED: escribir y ejecutar pruebas de los escenarios de API-01; guardar fallo funcional esperado.
- [ ] 2.1.2 GREEN: implementar mínimo comportamiento de API-01 y ejecutar las mismas pruebas.
- [ ] 2.1.3 REFACTOR: mejorar diseño, ejecutar suite afectada/typing/imports y registrar evidencia de API-01.
- [ ] 2.2.1 RED: escribir y ejecutar pruebas de los escenarios de AGT-01; guardar fallo funcional esperado.
- [ ] 2.2.2 GREEN: implementar mínimo comportamiento de AGT-01 y ejecutar las mismas pruebas.
- [ ] 2.2.3 REFACTOR: mejorar diseño, ejecutar suite afectada/typing/imports y registrar evidencia de AGT-01.
- [ ] 2.3.1 RED: escribir y ejecutar pruebas de los escenarios de AGT-02; guardar fallo funcional esperado.
- [ ] 2.3.2 GREEN: implementar mínimo comportamiento de AGT-02 y ejecutar las mismas pruebas.
- [ ] 2.3.3 REFACTOR: mejorar diseño, ejecutar suite afectada/typing/imports y registrar evidencia de AGT-02.
- [ ] 2.4.1 RED: escribir y ejecutar pruebas de los escenarios de AGT-03; guardar fallo funcional esperado.
- [ ] 2.4.2 GREEN: implementar mínimo comportamiento de AGT-03 y ejecutar las mismas pruebas.
- [ ] 2.4.3 REFACTOR: mejorar diseño, ejecutar suite afectada/typing/imports y registrar evidencia de AGT-03.

## 3. Cierre

- [ ] 3.1 Ejecutar tests de integración/seguridad pertinentes y checks estáticos; distinguir mocks de proveedores reales.
- [ ] 3.2 Actualizar documentación, trazabilidad y handoff; enlazar evidencia y commit.
- [ ] 3.3 Revisión del diff por revisor disponible, registrar autor y riesgos; integrar cuando Definition of Done esté satisfecha.
- [ ] 3.4 Archivar el cambio y promover deltas a specs sólo después de verificar implementación real.
