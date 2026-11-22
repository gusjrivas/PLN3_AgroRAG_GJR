## Why

La demo académica necesita mostrar tiempos y relación entre etapas de una consulta real.
OPS-01 y ADR-010 establecen los límites de observabilidad y privacidad.

## What Changes

- Agregar trazas OpenTelemetry opcionales de consola en la API local.
- Instrumentar consulta, recuperación, investigador y verificador con nombres fijos.

## Capabilities

### New Capabilities

- `academic-tracing`: trazas sanitizadas de la consulta para la demo local.

## Impact

API, aplicación, bootstrap, adaptador de infraestructura y dependencias opcionales.
