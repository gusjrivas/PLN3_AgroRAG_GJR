# Proposal: PoC productiva containerizada

## Why

AgroRAG V1 funciona localmente, pero depende del toolchain Python, rutas y procesos del host. V2
debe producir artefactos OCI reproducibles, ejecutarse con Docker Compose en un host Linux y
preservar todos los contratos funcionales, de evidencia y seguridad existentes.

## What Changes

- La configuración MUST aceptar secretos montados mediante `*_FILE` sin exponerlos.
- API y UI MUST construirse como imágenes separadas, mínimas y no root desde el mismo código.
- Compose MUST separar runtime, administración, gateway y evaluación adversarial.
- El catálogo MUST persistir, ser read-only para API y escribible sólo por el job administrativo.
- Producción MUST exponer únicamente el gateway y aplicar configuración/secretos externos.
- CI MUST validar imágenes, Compose, supply chain, regresión funcional y rollback.
- Garak MUST evaluar black-box la release candidata, con política y evidencia reproducibles.

## Capabilities

### New Capabilities

- `containerized-production-poc`: empaquetado, operación, seguridad y evaluación de la PoC V2.

### Modified Capabilities

Ninguna capacidad de negocio cambia. Los contratos HTTP, retrieval, agentes, UI, corpus y
evaluación existentes se preservan.

## Impact

Responsable: coordinador de arquitectura; revisión inicial por la misma sesión, revisión humana en
el MR. Rama: `feat/v2-container-foundation`. Propiedad inicial: `src/agro_rag/bootstrap/`,
`src/agro_rag_ui/`, tests de configuración/arquitectura/contenedores, `Dockerfile*`,
`compose*.yaml`, `.dockerignore`, `infra/`, workflows, documentación y evidencia V2.

No se modifican `Teoria*`, prompts, retrieval default, esquemas HTTP ni el corpus como consecuencia
implícita de containerizar. Decisión: ADR-015. Plan: `docs/plan-v2-production-poc.md`.
