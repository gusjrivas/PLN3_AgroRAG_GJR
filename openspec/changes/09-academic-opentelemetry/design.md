## Context

La API ya registra estado HTTP y la aplicación emite auditoría cerrada según ADR-010.

## Goals / Non-Goals

Mostrar la ejecución de la consulta y sus etapas desde una terminal local.

## Decisions

Bootstrap compone un proveedor por ciclo de vida de FastAPI y lo cierra al terminar.
El adaptador usa instrumentación manual y un recurso fijo. La aplicación conoce sólo
un puerto contextual para etapas, limitado a la consulta en curso. La recuperación incluye
el acceso a caché; los spans de agentes miden sus llamadas al modelo.

## Risks / Trade-offs

La salida de consola es síncrona y adecuada para una demo local de bajo volumen.
