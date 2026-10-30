# Tasks: Base independiente Python y TDD

Responsable: Coordinador/backend. Dependencias: Ninguna; primera etapa de implementación. Implementación y controles locales completados. Evidencia: docs/evidence/tdd/00-foundation.md. El merge requiere CI remota verde.

Reconciliación 29/10/2026: implementación y CI están integradas. Sólo queda el archivo formal del
cambio; se difiere a una auditoría de archivo conjunta de 00–05 para no mezclarla con el cierre 06.

## 1. Preparación

- [x] 1.1 Leer ADR aplicables, fijar archivos de propiedad y comprobar dependencias.
- [x] 1.2 Preparar fixtures/contratos sin servicios pagos; identificar qué checks requieren integración real.

## 2. Implementación mediante TDD

- [x] 2.1.1 Verificar FND-01 por inspección Git; no corresponde fabricar un RED para un clon ya creado.
- [x] 2.1.2 GREEN: implementar mínimo comportamiento de FND-01 y ejecutar las mismas pruebas.
- [x] 2.1.3 REFACTOR: mejorar diseño, ejecutar suite afectada/typing/imports y registrar evidencia de FND-01.
- [x] 2.2.1 RED: escribir y ejecutar pruebas de los escenarios de FND-02; guardar fallo funcional esperado.
- [x] 2.2.2 GREEN: implementar mínimo comportamiento de FND-02 y ejecutar las mismas pruebas.
- [x] 2.2.3 REFACTOR: mejorar diseño, ejecutar suite afectada/typing/imports y registrar evidencia de FND-02.
- [x] 2.3.1 RED: escribir y ejecutar pruebas de los escenarios de FND-03; guardar fallo funcional esperado.
- [x] 2.3.2 GREEN: implementar mínimo comportamiento de FND-03 y ejecutar las mismas pruebas.
- [x] 2.3.3 REFACTOR: mejorar diseño, ejecutar suite afectada/typing/imports y registrar evidencia de FND-03.

## 3. Cierre

- [x] 3.1 Ejecutar tests de integración/seguridad pertinentes y checks estáticos; distinguir mocks de proveedores reales.
- [x] 3.2 Actualizar documentación, trazabilidad y handoff; enlazar evidencia y commit.
- [x] 3.3 Revisión del diff por revisor disponible, registrar autor y riesgos; integrar cuando Definition of Done esté satisfecha.
- [ ] 3.4 Archivar el cambio y promover deltas a specs sólo después de verificar implementación real.
