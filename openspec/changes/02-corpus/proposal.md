# Proposal: Corpus versionado con evidencia

## Why

Avanzar el TP AgroRAG independiente con calidad preproductiva, Python y TDD. Esta etapa cubre COR-01, COR-02, COR-03 y sus escenarios observables, conforme a docs/requirements.md.

## What Changes

- La ingesta MUST aceptar sólo fuentes curadas con hash, edición, estado de derechos y páginas seleccionadas verificadas.
- La extracción MUST conservar asociación de valores, unidades, cultivo y condiciones en toda tabla usada como evidencia.
- El corpus MUST usar IDs inmutables y activación atómica sólo cuando catálogo e índice de la nueva versión estén verificados.

## Capabilities

### New Capabilities

- `corpus`: corpus versionado con evidencia.

### Modified Capabilities

Ninguna capacidad vigente. Se trata de implementación inicial aún pendiente.

## Impact

Propietario: RAG/datos. Rutas objetivo: src/agro_rag/infrastructure/ingestion y catalog; data/corpus; tests/unit/ingestion; tests/integration/catalog. Dependencias: 00-foundation y 01-engram; puede continuar desde Git si memoria tiene bloqueo documentado. Decisiones: ADR-005, ADR-006.
No modificar el repositorio docente. No ampliar a sensores, riego automático, fine-tuning o infraestructura productiva completa. No marcar esta propuesta como implementada por estar validada su sintaxis.
