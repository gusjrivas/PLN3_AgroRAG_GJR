# Design: PoC productiva containerizada

## Context

FastAPI y Streamlit ya están separados por HTTP. Bootstrap ensambla proveedores y carga un catálogo
SQLite versionado; UI no importa backend. V2 convierte esos límites existentes en unidades de
despliegue sin transformar módulos en microservicios.

## Goals / Non-Goals

El objetivo es una PoC single-host reproducible, endurecida y operable con Compose, manteniendo V1
compatible durante la migración. No se promete alta disponibilidad, cero downtime, multiusuario,
Kubernetes ni cumplimiento regulatorio.

## Decisions

Aplicar ADR-015: targets OCI separados `api`/`ui`, gateway único, job `catalogue-admin`, volumen
versionado, overlays dev/production/security, secretos por archivo, procesos no root y release por
digest. Garak vive en una imagen/job separado y ataca el gateway de staging, no el proveedor
directo.

Los cambios se integran por fases. Cada fase mantiene pruebas de regresión locales y CI. Ninguna
imagen descarga pesos o construye índices durante startup. Los artefactos garak crudos son
restringidos porque contienen prompts y respuestas.

## Data and contracts

El catálogo activo mantiene `active.json` y snapshots SQLite existentes. API sólo lo lee; el CLI
administrativo conserva la escritura. UI usa `http://api:8000` dentro de Compose. Secretos admiten
valor directo sólo en desarrollo y archivo montado en despliegues; configurar ambos o un archivo
ausente/vacío falla cerrado sin revelar contenido.

## TDD and verification

Los escenarios están en `specs/containerized-production-poc/spec.md`. Cada comportamiento nuevo
registra RED/GREEN/REFACTOR en `docs/evidence/tdd`. Config/Compose/Docker se verifican con tests
ejecutables, inspección de imágenes y E2E offline. Los scans reales de garak se separan de tests con
fixtures y requieren presupuesto/autorización de proveedor.

## Dependencies and rollout

Orden: configuración y entrypoints; imágenes; Compose/catálogo; overlay productivo; CI/staging;
garak; promoción. V1 sigue disponible hasta que el stack Compose, persistencia, rollback y suites
existentes aprueben. Rollback restaura digest y manifiesto previo, sin borrar el volumen activo.

## Risks / trade-offs

Un host y una réplica son puntos únicos de falla. Imágenes semánticas pueden ser grandes. Garak
produce falsos positivos/negativos y consume API. Estos límites se mitigan con BM25 por defecto,
perfiles opcionales, límites de recursos, baseline por detector, triage humano y documentación
explícita; no se presentan como garantías.
