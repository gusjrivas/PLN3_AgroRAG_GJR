## Why

La demo necesita mostrar la duración de una consulta de AgroRAG y de sus etapas, y observar tendencias durante el uso de Streamlit. La candidata académica se identifica con el tag local `demo-materia-2026-11-23-rc1` en `d0111a3`.

## What Changes

- Agregar una modalidad OTLP explícita a la instrumentación manual de la API.
- Exponer métricas de volumen, latencia HTTP, resultados y caché de recuperación.
- Provisionar un tablero Grafana mediante un Compose adicional para desarrollo y demo.
- Registrar evidencia de TDD y de la prueba integrada antes de proponer el merge.

## Capabilities

### New Capabilities

- `local-observability`: trazas y métricas sanitizadas en Grafana local.

## Impact

Configuración, bootstrap, instrumentación de aplicación e infraestructura, dependencias opcionales, Docker y runbook. El alcance de despliegue es la demo local. La reescritura del informe y la presentación se hará después del cierre técnico.
