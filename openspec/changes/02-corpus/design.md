# Design: Corpus versionado con evidencia

## Context

Proyecto nuevo PLN3_AgroRAG_GJR. Contratos comunes: docs/architecture.md y docs/contracts.md. Requisitos: COR-01, COR-02, COR-03. Estado: propuesta, sin comportamiento implementado.

## Goals / Non-Goals

Implementar los escenarios de specs/corpus/spec.md con tests previos y evidencia. Esta etapa no autoriza funcionalidades fuera del MVP ni modificar PLN3_GJR.

## Decisions

Aplicar ADR-005, ADR-006; consultar docs/adr/README.md y los archivos individuales. Dueño: RAG/datos. Rutas: src/agro_rag/infrastructure/ingestion y catalog; data/corpus; tests/unit/ingestion; tests/integration/catalog. El coordinador controla cambios en contratos, lockfile y configuración. Aplicar puertos inyectables y no inicializar recursos externos en import.

## Data and contracts

Consumir los contratos de docs/contracts.md y metadatos de docs/corpus.md cuando corresponda. Mantener identidad de evidencia y versión entre capas; errores operativos tipados. Todas las decisiones de negocio de esta etapa están expresadas en sus escenarios. Detalles de testing: docs/tdd.md; memoria: docs/setup-engram.md; UI: docs/frontend.md; evaluación: docs/evaluation.md.

## TDD and verification

Cada escenario tiene ID estable. Escribir primero el test de comportamiento indicado en test-plan.md, ejecutar RED, implementar GREEN y refactorizar manteniendo la suite. Para setup Engram y entrega documental usar verificación operativa/revisión real; cualquier script ejecutable añadido sigue TDD. No inventar tests rojos para operaciones manuales ni resultados del producto.

## Dependencies and rollout

00-foundation y 01-engram; puede continuar desde Git si memoria tiene bloqueo documentado. Primera integración en rama de tarea con revisión del diff. No activar corpus ni sustituir contratos hasta pasar sus pruebas. Revertir el commit de tarea y conservar evidencia si falla un gate. Datos/índices versionados permiten restaurar manifiesto activo anterior; no destruir versiones para ocultar resultados.

## Risks / trade-offs

Consultar docs/plan.md. Si un proveedor o recurso local falta, las pruebas offline pueden continuar, pero integración real queda pendiente. Cambiar un modelo o contrato exige actualizar ADR/spec y repetir pruebas afectadas. Una memoria Engram no permite sobrepasar estas condiciones.
