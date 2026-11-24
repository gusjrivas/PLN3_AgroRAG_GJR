## Why

El tablero local necesita mostrar el uso de tokens de los dos agentes y su costo estimado.

## What Changes

- Exportar cantidades de entrada y salida para cada llamada con conteos válidos.
- Mostrar cantidad y costo aproximado en Grafana con tarifas editables en USD por millón.

## Capabilities

### Modified Capabilities

- `local-observability`: métricas de tokens y cálculo del costo en el tablero.

## Impact

Instrumentación opcional de la API, tablero y runbook local.
