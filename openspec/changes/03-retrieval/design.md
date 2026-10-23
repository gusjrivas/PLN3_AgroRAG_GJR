# Design: Recuperación híbrida y reranking evaluables

## Context

Proyecto nuevo PLN3_AgroRAG_GJR. Contratos comunes: docs/architecture.md y docs/contracts.md. Requisitos: RET-01, RET-02, RET-03. Estado: contratos y adaptadores administrativos implementados; activación y evaluación real pendientes.

## Goals / Non-Goals

Implementar los escenarios de specs/retrieval/spec.md con tests previos y evidencia. Esta etapa no autoriza funcionalidades fuera del MVP ni modificar PLN3_GJR.

## Decisions

Aplicar ADR-005, ADR-006, ADR-010; consultar docs/adr/README.md y los archivos individuales. Dueño: RAG/datos. Rutas: application/ports; infrastructure/retrieval; tests/unit/retrieval; tests/integration/retrieval. El coordinador controla cambios en contratos, lockfile y configuración. Aplicar puertos inyectables y no inicializar recursos externos en import.

## Data and contracts

Consumir los contratos de docs/contracts.md y metadatos de docs/corpus.md cuando corresponda. Mantener identidad de evidencia y versión entre capas; errores operativos tipados. Todas las decisiones de negocio de esta etapa están expresadas en sus escenarios. Detalles de testing: docs/tdd.md; memoria: docs/setup-engram.md; UI: docs/frontend.md; evaluación: docs/evaluation.md.

## TDD and verification

Cada escenario tiene ID estable. Escribir primero el test de comportamiento indicado en test-plan.md, ejecutar RED, implementar GREEN y refactorizar manteniendo la suite. Para setup Engram y entrega documental usar verificación operativa/revisión real; cualquier script ejecutable añadido sigue TDD. No inventar tests rojos para operaciones manuales ni resultados del producto.

## Dependencies and rollout

02-corpus. Primera integración en rama de tarea con revisión del diff. No activar corpus ni sustituir contratos hasta pasar sus pruebas. Revertir el commit de tarea y conservar evidencia si falla un gate. Datos/índices versionados permiten restaurar manifiesto activo anterior; no destruir versiones para ocultar resultados.

## Risks / trade-offs

Consultar docs/plan.md. Si un proveedor o recurso local falta, las pruebas offline pueden continuar, pero integración real queda pendiente. Cambiar un modelo o contrato exige actualizar ADR/spec y repetir pruebas afectadas. Una memoria Engram no permite sobrepasar estas condiciones.

## Corte de contratos del 22/10/2026

ADR-013 concreta el diseño del pipeline puro: puertos CandidateRanker/Reranker/TokenCounter, identidad IndexIdentity, resultado inmutable con rankings por etapa, filtros de corpus/cultivo y presupuesto de contexto serializado. El adaptador lexical entrega candidatos sin recorte de diversidad previo. La composición del producto continúa lexical hasta validar adaptadores reales. Ver docs/evidence/tdd/03-pipeline.md; RET-02-e5 y las integraciones científicas siguen pendientes.

## Corte de adaptadores del 23/10/2026

El ejemplo fijado de `PLN3_GJR/Teoria1/Codigo/RAG` se adapta a `PineconeVectorRanker`,
`E5Embedder` y `CrossEncoderReranker`. Los modelos y el SDK se cargan sólo desde bootstrap
administrativo. La ingesta usa IDs del catálogo, metadata mínima, namespace fresco y manifiesto
publicado después de verificar visibilidad. La API no cambia de modo; `integration_live`, tokenizer
real y benchmark siguen siendo puertas de activación.
