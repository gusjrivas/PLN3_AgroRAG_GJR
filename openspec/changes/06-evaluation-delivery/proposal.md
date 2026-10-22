# Proposal: Evaluación y entrega académica reproducibles

## Why

Avanzar el TP AgroRAG independiente con calidad preproductiva, Python y TDD. Esta etapa cubre EVA-01, EVA-02, DEL-01 y sus escenarios observables, conforme a docs/requirements.md.

## What Changes

- El benchmark MUST contener 60 casos revisados con split agrupado 30 dev/30 test y evidencia fuente; parámetros SHALL seleccionarse sólo con dev.
- La evaluación MUST separar recuperación, generación, agentes y operación, y distinguir ejecuciones reales de dobles de prueba.
- La entrega MUST incluir código reproducible, informe PDF y demo de 15 minutos con limitaciones y atribución de asistencia de IA.

## Capabilities

### New Capabilities

- `evaluation-delivery`: evaluación y entrega académica reproducibles.

### Modified Capabilities

Ninguna capacidad vigente. Se trata de implementación inicial aún pendiente.

## Impact

Propietario: Evaluador y coordinador. Rutas objetivo: scripts/evaluation; data/evaluation; docs/report; docs/evidence; tests/unit/metrics. Dependencias: 05-frontend-hardening; anotación puede iniciar tras 02. Decisiones: ADR-008, ADR-011.
No modificar el repositorio docente. No ampliar a sensores, riego automático, fine-tuning o infraestructura productiva completa. No marcar esta propuesta como implementada por estar validada su sintaxis.
