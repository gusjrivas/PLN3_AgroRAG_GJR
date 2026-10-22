# Proposal: Interfaz Python, seguridad y optimización

## Why

Avanzar el TP AgroRAG independiente con calidad preproductiva, Python y TDD. Esta etapa cubre UI-01, UI-02, SEC-01, OPS-01 y sus escenarios observables, conforme a docs/requirements.md.

## What Changes

- La UI Streamlit MUST consumir sólo HTTP y mostrar estados de negocio, errores y evidencia de forma accesible.
- La UI MUST aislar sesiones y ejecutar una llamada por envío, sin repetir inferencia en reruns.
- El producto MUST aplicar controles de acceso, herramientas permitidas y validación de evidencia sin ejecutar instrucciones del corpus.
- Retrieval MUST cachear con identidad de corpus/modelo/config y registrar tiempos, uso y decisiones sin secretos.

## Capabilities

### New Capabilities

- `frontend-hardening`: interfaz python, seguridad y optimización.

### Modified Capabilities

Ninguna capacidad vigente. Se trata de implementación inicial aún pendiente.

## Impact

Propietario: Frontend y revisor. Rutas objetivo: src/agro_rag_ui; infraestructura/cache y audit; api/auth; tests/ui; tests/e2e; infra. Dependencias: 04-agents-backend; UI puede preparar fixtures desde contratos congelados. Decisiones: ADR-004, ADR-008, ADR-009, ADR-010.
No modificar el repositorio docente. No ampliar a sensores, riego automático, fine-tuning o infraestructura productiva completa. No marcar esta propuesta como implementada por estar validada su sintaxis.
