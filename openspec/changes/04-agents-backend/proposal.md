# Proposal: API y colaboración de dos agentes

## Why

Avanzar el TP AgroRAG independiente con calidad preproductiva, Python y TDD. Esta etapa cubre API-01, AGT-01, AGT-02, AGT-03 y sus escenarios observables, conforme a docs/requirements.md.

## What Changes

- La API MUST validar QueryRequest y devolver QueryResponse o ErrorResponse según docs/contracts.md, sin mezclar fallos operativos con estados de negocio.
- El investigador y verificador MUST intercambiar resultados estructurados y permitir una ronda de corrección basada en evidencias.
- Una respuesta answered MUST respaldar cada claim con evidence_ids válidos; falta de datos SHALL producir aclaración y falta de soporte SHALL producir abstención.
- La orquestación MUST respetar límites globales de llamadas, búsquedas, tokens y deadline, incluidos reintentos.

## Capabilities

### New Capabilities

- `agents-backend`: api y colaboración de dos agentes.

### Modified Capabilities

Ninguna capacidad vigente. Se trata de implementación inicial aún pendiente.

## Impact

Propietario: Backend/agentes. Rutas objetivo: application/use_cases; infrastructure/agents; api; bootstrap; tests/contract; tests/unit/agents. Dependencias: 03-retrieval. Decisiones: ADR-003, ADR-007, ADR-009.
No modificar el repositorio docente. No ampliar a sensores, riego automático, fine-tuning o infraestructura productiva completa. No marcar esta propuesta como implementada por estar validada su sintaxis.
