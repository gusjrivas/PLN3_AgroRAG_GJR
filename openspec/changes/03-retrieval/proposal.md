# Proposal: Recuperación híbrida y reranking evaluables

## Why

Avanzar el TP AgroRAG independiente con calidad preproductiva, Python y TDD. Esta etapa cubre RET-01, RET-02, RET-03 y sus escenarios observables, conforme a docs/requirements.md.

## What Changes

- El sistema MUST ofrecer modos BM25, vectorial, híbrido RRF e híbrido con reranker sobre un corpus y conjunto de chunks comunes.
- Los embeddings MUST aplicar los prefijos requeridos y verificar modelo, revisión, dimensión y corpus_version; reranker SHALL evaluarse en español antes de selección.
- El contexto MUST limitar fragmentos por source_id y tokens reales, y sólo incluir evidencias resolubles de la versión activa.

## Capabilities

### New Capabilities

- `retrieval`: recuperación híbrida y reranking evaluables.

### Modified Capabilities

Ninguna capacidad vigente. Se trata de implementación inicial aún pendiente.

## Impact

Propietario: RAG/datos. Rutas objetivo: application/ports; infrastructure/retrieval; tests/unit/retrieval; tests/integration/retrieval. Dependencias: 02-corpus. Decisiones: ADR-005, ADR-006, ADR-010.
No modificar el repositorio docente. No ampliar a sensores, riego automático, fine-tuning o infraestructura productiva completa. No marcar esta propuesta como implementada por estar validada su sintaxis.
