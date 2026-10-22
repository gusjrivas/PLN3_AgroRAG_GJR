# Proposal: Base independiente Python y TDD

## Why

Avanzar el TP AgroRAG independiente con calidad preproductiva, Python y TDD. Esta etapa cubre FND-01, FND-02, FND-03 y sus escenarios observables, conforme a docs/requirements.md.

## What Changes

- El proyecto MUST inicializarse como repositorio independiente PLN3_AgroRAG_GJR y documentar el código docente incorporado sin modificar PLN3_GJR.
- El backend MUST separar dominio, aplicación, infraestructura, API y bootstrap; el frontend SHALL depender exclusivamente del contrato HTTP.
- Todo cambio de comportamiento MUST tener test rojo previo, verde y refactor documentados; dependencias SHALL fijarse con uv.lock y checks automáticos.

## Capabilities

### New Capabilities

- `foundation`: base independiente python y tdd.

### Modified Capabilities

Ninguna capacidad vigente. Se trata de implementación inicial aún pendiente.

## Impact

Propietario: Coordinador/backend. Rutas objetivo: src/agro_rag/domain, application, api, bootstrap; tests/architecture; pyproject.toml; uv.lock; .github/workflows. Dependencias: Ninguna; primera etapa de implementación. Decisiones: ADR-001, ADR-003, ADR-008.
No modificar el repositorio docente. No ampliar a sensores, riego automático, fine-tuning o infraestructura productiva completa. No marcar esta propuesta como implementada por estar validada su sintaxis.
